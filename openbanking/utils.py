import re
import requests
from datetime import date, timedelta, datetime
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


def parse_kb_sms(sms_body: str) -> dict | None:
    """
    KB 입금 문자 파싱.
    형식:
      [Web발신]
      [KB]05/26 11:20
      772601**471
      박종석
      입금
      74,727
      잔액9,600,434
    """
    if "[KB]" not in sms_body or "입금" not in sms_body:
        return None

    lines = [l.strip() for l in sms_body.strip().splitlines() if l.strip()]

    try:
        # 날짜/시간: [KB]05/26 11:20
        dt_line = next(l for l in lines if l.startswith("[KB]"))
        dt_str = dt_line.replace("[KB]", "").strip()  # "05/26 11:20"
        month, day = dt_str[:5].split("/")
        hour, minute = dt_str[6:].split(":")
        year = date.today().year
        tran_date = date(year, int(month), int(day))
        tran_time = f"{int(hour):02d}{int(minute):02d}00"

        # 입금 라인 인덱스 찾기
        deposit_idx = next(i for i, l in enumerate(lines) if l == "입금")

        # 입금자명: 입금 바로 위 줄
        depositor = lines[deposit_idx - 1]

        # 금액: 입금 바로 아래 줄 (쉼표 제거)
        amount_str = lines[deposit_idx + 1].replace(",", "").replace("원", "").strip()
        amount = int(amount_str)

        # 잔액
        balance_line = next((l for l in lines if l.startswith("잔액")), "")
        balance = int(balance_line.replace("잔액", "").replace(",", "").replace("원", "")) if balance_line else 0

        return {
            "tran_date": tran_date,
            "tran_time": tran_time,
            "depositor": depositor,
            "amount": amount,
            "balance": balance,
        }
    except Exception:
        return None


def match_sms_transaction(parsed: dict):
    """파싱된 SMS로 BankTransaction 저장 + 출고 자동 매칭"""
    unique_no = f"SMS_{parsed['tran_date'].strftime('%Y%m%d')}_{parsed['tran_time']}_{parsed['amount']}_{parsed['depositor']}"

    tran, created = BankTransaction.objects.get_or_create(
        tran_unique_no=unique_no,
        defaults={
            "account": _get_sms_account(),
            "tran_date": parsed["tran_date"],
            "tran_time": parsed["tran_time"],
            "tran_type": "D",
            "tran_amt": parsed["amount"],
            "balance_amt": parsed["balance"],
            "print_content": parsed["depositor"],
        },
    )

    matched_release = None
    if created:
        unpaid = MaterialRelease.objects.filter(payment_status="unpaid").select_related("institution")
        matched_release = _find_best_match(tran, unpaid)
        if matched_release:
            tran.matched_release = matched_release
            tran.is_auto_matched = True
            tran.save(update_fields=["matched_release", "is_auto_matched"])
            matched_release.payment_status = "paid"
            matched_release.payment_date = parsed["tran_date"]
            matched_release.save(update_fields=["payment_status", "payment_date"])

    return tran, matched_release


def _get_sms_account():
    """SMS 수신용 가상 계좌 객체 반환 (없으면 생성)"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    account, _ = RegisteredAccount.objects.get_or_create(
        fintech_use_num="SMS_KB_DIRECT",
        defaults={
            "user": user,
            "bank_code": "004",
            "bank_name": "KB국민은행",
            "account_num_masked": "SMS수신",
            "account_holder": "SMS",
        },
    )
    return account
