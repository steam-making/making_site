import os
import uuid
import urllib.parse
import requests
from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from materials.models import MaterialRelease
from .models import BankTransaction, OpenBankingToken, RegisteredAccount
from .utils import auto_match_transactions, fetch_and_save_transactions

OPENBANKING_BASE = "https://testapi.openbanking.or.kr"  # 테스트
# 운영: https://openapi.openbanking.or.kr


def _get_client():
    return {
        "client_id": settings.OPENBANKING_CLIENT_ID,
        "client_secret": settings.OPENBANKING_CLIENT_SECRET,
        "redirect_uri": settings.OPENBANKING_REDIRECT_URI,
    }


@login_required
def auth_start(request):
    """오픈뱅킹 OAuth 인증 시작 — 금융결제원 인증 페이지로 리다이렉트"""
    client = _get_client()
    state = str(uuid.uuid4())
    request.session["openbanking_state"] = state
    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client["client_id"],
        "redirect_uri": client["redirect_uri"],
        "scope": "login inquiry",
        "state": state,
        "auth_type": "0",
    }, quote_via=urllib.parse.quote)  # 공백을 +가 아닌 %20으로 인코딩
    return redirect(f"{OPENBANKING_BASE}/oauth/2.0/authorize?{params}")


@login_required
def auth_callback(request):
    """OAuth 콜백 — code로 access_token 교환 후 저장"""
    code = request.GET.get("code")
    state = request.GET.get("state")
    error = request.GET.get("error")

    if error or not code:
        messages.error(request, f"오픈뱅킹 인증 실패: {error or '코드 없음'}")
        return redirect("openbanking_dashboard")

    if state != request.session.get("openbanking_state"):
        messages.error(request, "보안 오류: state 불일치")
        return redirect("openbanking_dashboard")

    client = _get_client()
    resp = requests.post(
        f"{OPENBANKING_BASE}/oauth/2.0/token",
        data={
            "code": code,
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "redirect_uri": client["redirect_uri"],
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    data = resp.json()
    if "access_token" not in data:
        messages.error(request, f"토큰 발급 실패: {data.get('error_description', data)}")
        return redirect("openbanking_dashboard")

    expires_at = timezone.now() + timedelta(seconds=int(data.get("expires_in", 7776000)))
    OpenBankingToken.objects.update_or_create(
        user=request.user,
        defaults={
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", ""),
            "expires_at": expires_at,
            "user_seq_no": data.get("user_seq_no", ""),
        },
    )
    messages.success(request, "오픈뱅킹 인증 완료! 계좌를 등록해 주세요.")
    return redirect("openbanking_accounts")


@login_required
def account_list(request):
    """등록된 계좌 목록 조회 및 오픈뱅킹에서 계좌 가져오기"""
    try:
        token_obj = request.user.openbanking_token
    except OpenBankingToken.DoesNotExist:
        messages.warning(request, "먼저 오픈뱅킹 인증을 완료해 주세요.")
        return redirect("openbanking_dashboard")

    if request.method == "POST" and request.POST.get("action") == "fetch_accounts":
        # 오픈뱅킹에서 연결된 계좌 목록 가져오기
        resp = requests.get(
            f"{OPENBANKING_BASE}/v2.0/user/me",
            headers={"Authorization": f"Bearer {token_obj.access_token}"},
            params={"user_seq_no": token_obj.user_seq_no},
            timeout=10,
        )
        data = resp.json()
        res_list = data.get("res_list", [])
        created = 0
        for acc in res_list:
            _, is_new = RegisteredAccount.objects.get_or_create(
                fintech_use_num=acc["fintech_use_num"],
                defaults={
                    "user": request.user,
                    "bank_code": acc.get("bank_code_std", ""),
                    "bank_name": acc.get("bank_name", ""),
                    "account_num_masked": acc.get("account_num_masked", ""),
                    "account_holder": acc.get("account_holder_name", ""),
                },
            )
            if is_new:
                created += 1
        messages.success(request, f"계좌 {len(res_list)}개 조회, {created}개 신규 등록")
        return redirect("openbanking_accounts")

    accounts = RegisteredAccount.objects.filter(user=request.user)
    return render(request, "openbanking/account_list.html", {"accounts": accounts})


@login_required
@require_POST
def sync_transactions(request):
    """선택한 계좌의 최근 거래내역 동기화 + 자동 매칭"""
    account_id = request.POST.get("account_id")
    days = int(request.POST.get("days", 30))

    try:
        account = RegisteredAccount.objects.get(id=account_id, user=request.user)
        token_obj = request.user.openbanking_token
    except (RegisteredAccount.DoesNotExist, OpenBankingToken.DoesNotExist):
        return JsonResponse({"success": False, "message": "계좌 또는 토큰을 찾을 수 없습니다."})

    try:
        saved, skipped = fetch_and_save_transactions(account, token_obj, days=days)
        matched = auto_match_transactions(account)
        return JsonResponse({
            "success": True,
            "message": f"거래내역 {saved}건 저장 (중복 {skipped}건 제외), 자동매칭 {matched}건",
            "saved": saved,
            "matched": matched,
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


@login_required
def transaction_list(request):
    """거래내역 + 매칭 현황"""
    accounts = RegisteredAccount.objects.filter(user=request.user, is_active=True)
    selected_account_id = request.GET.get("account")

    transactions = BankTransaction.objects.select_related(
        "account", "matched_release__institution"
    ).filter(account__user=request.user, tran_type="D")  # D=입금만

    if selected_account_id:
        transactions = transactions.filter(account_id=selected_account_id)

    # 미매칭 입금만 필터
    only_unmatched = request.GET.get("unmatched") == "1"
    if only_unmatched:
        transactions = transactions.filter(matched_release__isnull=True)

    transactions = transactions[:200]

    return render(request, "openbanking/transaction_list.html", {
        "accounts": accounts,
        "transactions": transactions,
        "selected_account_id": selected_account_id,
        "only_unmatched": only_unmatched,
    })


@login_required
@require_POST
def manual_match(request):
    """수동 매칭: 거래 ↔ MaterialRelease 연결 후 수금 처리"""
    tran_id = request.POST.get("transaction_id")
    release_id = request.POST.get("release_id")

    try:
        tran = BankTransaction.objects.get(id=tran_id, account__user=request.user)
        release = MaterialRelease.objects.get(id=release_id)
    except (BankTransaction.DoesNotExist, MaterialRelease.DoesNotExist):
        return JsonResponse({"success": False, "message": "데이터를 찾을 수 없습니다."})

    tran.matched_release = release
    tran.is_auto_matched = False
    tran.save(update_fields=["matched_release", "is_auto_matched"])

    release.payment_status = "paid"
    release.payment_date = tran.tran_date
    release.save(update_fields=["payment_status", "payment_date"])

    return JsonResponse({"success": True, "message": "매칭 완료 및 수금 처리됐습니다."})


@login_required
@require_POST
def unmatch_transaction(request):
    """매칭 취소"""
    tran_id = request.POST.get("transaction_id")
    try:
        tran = BankTransaction.objects.get(id=tran_id, account__user=request.user)
    except BankTransaction.DoesNotExist:
        return JsonResponse({"success": False, "message": "거래를 찾을 수 없습니다."})

    release = tran.matched_release
    tran.matched_release = None
    tran.is_auto_matched = False
    tran.save(update_fields=["matched_release", "is_auto_matched"])

    if release:
        # 해당 release에 연결된 다른 매칭 거래가 없으면 미수금으로 되돌림
        if not release.bank_transactions.exists():
            release.payment_status = "unpaid"
            release.payment_date = None
            release.save(update_fields=["payment_status", "payment_date"])

    return JsonResponse({"success": True, "message": "매칭이 취소됐습니다."})


@login_required
def dashboard(request):
    has_token = OpenBankingToken.objects.filter(user=request.user).exists()
    accounts = RegisteredAccount.objects.filter(user=request.user, is_active=True)
    recent_matched = BankTransaction.objects.filter(
        account__user=request.user,
        matched_release__isnull=False,
    ).select_related("matched_release__institution")[:10]
    unmatched_count = BankTransaction.objects.filter(
        account__user=request.user,
        tran_type="D",
        matched_release__isnull=True,
    ).count()

    return render(request, "openbanking/dashboard.html", {
        "has_token": has_token,
        "accounts": accounts,
        "recent_matched": recent_matched,
        "unmatched_count": unmatched_count,
    })
