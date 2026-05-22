import requests
from datetime import date, timedelta
from django.utils import timezone

from materials.models import MaterialRelease
from .models import BankTransaction, RegisteredAccount, OpenBankingToken

OPENBANKING_BASE = "https://openapi.openbanking.or.kr"


def fetch_and_save_transactions(account: RegisteredAccount, token_obj: OpenBankingToken, days: int = 30):
    """오픈뱅킹 API로 거래내역 조회 후 저장. (saved, skipped) 반환"""
    from_date = (date.today() - timedelta(days=days)).strftime("%Y%m%d")
    to_date = date.today().strftime("%Y%m%d")

    resp = requests.get(
        f"{OPENBANKING_BASE}/v2.0/account/transaction_list/fin_num",
        headers={"Authorization": f"Bearer {token_obj.access_token}"},
        params={
            "bank_tran_id": _make_tran_id(token_obj),
            "fintech_use_num": account.fintech_use_num,
            "inquiry_type": "A",       # A=전체
            "inquiry_base": "D",       # D=날짜기준
            "from_date": from_date,
            "to_date": to_date,
            "sort_order": "D",         # D=최신순
            "tran_dtime": timezone.now().strftime("%Y%m%d%H%M%S"),
        },
        timeout=15,
    )
    data = resp.json()

    if data.get("rsp_code") not in ("A0000", "O0000"):
        raise Exception(f"API 오류: {data.get('rsp_message', data)}")

    saved = 0
    skipped = 0
    for t in data.get("res_list", []):
        unique_no = t.get("tran_unique_no") or f"{account.fintech_use_num}_{t['tran_date']}_{t['tran_time']}_{t['tran_amt']}"
        _, created = BankTransaction.objects.get_or_create(
            tran_unique_no=unique_no,
            defaults={
                "account": account,
                "tran_date": _parse_date(t["tran_date"]),
                "tran_time": t.get("tran_time", ""),
                "tran_type": t.get("inout_type", ""),  # D=입금, W=출금
                "tran_amt": int(t.get("tran_amt", 0)),
                "balance_amt": int(t.get("after_balance_amt", 0)),
                "print_content": t.get("print_content", ""),
                "branch_name": t.get("branch_name", ""),
            },
        )
        if created:
            saved += 1
        else:
            skipped += 1

    return saved, skipped


def auto_match_transactions(account: RegisteredAccount) -> int:
    """입금 거래내역을 출고 그룹과 자동 매칭. 매칭된 건수 반환"""
    unmatched = BankTransaction.objects.filter(
        account=account,
        tran_type="D",
        matched_release__isnull=True,
    )

    # 미수금 출고 목록: (기관명, 합계금액, 월) → release
    unpaid_releases = MaterialRelease.objects.filter(
        payment_status="unpaid"
    ).select_related("institution")

    matched_count = 0
    for tran in unmatched:
        best = _find_best_match(tran, unpaid_releases)
        if best:
            tran.matched_release = best
            tran.is_auto_matched = True
            tran.save(update_fields=["matched_release", "is_auto_matched"])
            best.payment_status = "paid"
            best.payment_date = tran.tran_date
            best.save(update_fields=["payment_status", "payment_date"])
            matched_count += 1

    return matched_count


def _find_best_match(tran: BankTransaction, releases):
    """
    매칭 우선순위:
    1. 입금자명에 기관명(또는 학교명) 포함 + 금액 일치
    2. 금액만 일치 (단독 금액인 경우)
    """
    content = tran.print_content.replace(" ", "")
    amount = tran.tran_amt

    # 기관명 + 금액 매칭 (가장 신뢰도 높음)
    for rel in releases:
        inst = rel.institution
        inst_name = (inst.name or "").replace(" ", "")
        school_name = (inst.school.name if inst.school else "").replace(" ", "")
        total = _release_total(rel)

        if total != amount:
            continue
        if inst_name and inst_name in content:
            return rel
        if school_name and school_name in content:
            return rel

    # 금액만 일치 (동일 금액 release가 1건뿐일 때만)
    amount_matches = [r for r in releases if _release_total(r) == amount]
    if len(amount_matches) == 1:
        return amount_matches[0]

    return None


def _release_total(release: MaterialRelease) -> int:
    from django.db.models import Sum, F
    total = release.items.aggregate(s=Sum(F('unit_price') * F('quantity')))["s"] or 0
    return int(total)


def _make_tran_id(token_obj: OpenBankingToken) -> str:
    import os
    from django.conf import settings
    client_id = getattr(settings, "OPENBANKING_CLIENT_ID", "")[:10]
    rand = os.urandom(4).hex().upper()[:9]
    return f"{client_id}U{rand}"


def _parse_date(date_str: str):
    from datetime import date as d
    return d(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
