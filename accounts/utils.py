# accounts/utils.py
import requests, json
from django.conf import settings
from django.utils import timezone
from accounts.models import KakaoToken

KAKAO_MEMO_SEND_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"

def _kakao_headers(access_token: str):
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
    }

def _refresh_token(token: KakaoToken) -> KakaoToken | None:
    try:
        resp = requests.post(
            KAKAO_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": settings.KAKAO_REST_API_KEY,
                "refresh_token": token.refresh_token,
            },
            timeout=10,
        )
        data = resp.json()
        print("🔄 토큰 갱신 응답:", data)
        if "access_token" in data:
            token.access_token = data["access_token"]
            # refresh_token이 함께 오면 갱신
            if "refresh_token" in data:
                token.refresh_token = data["refresh_token"]
            # 선택: expires_in 필드 쓰면 갱신시간 기록
            token.expires_in = data.get("expires_in", token.expires_in)
            token.save(update_fields=["access_token", "refresh_token", "expires_in"])
            return token
    except Exception as e:
        print("[카카오 토큰 갱신 오류]", e)
    return None

def send_kakao_message(user, text, local_test=False):
    try:
        token = KakaoToken.objects.filter(user=user).order_by("-created_at").first()
        if not token:
            print(f"[카카오 발송 실패] 토큰 없음: {user.username}")
            return {"error": "no_token"}

        link_url = "http://127.0.0.1:8000" if local_test else "http://133.186.144.151"
        template_obj = {
            "object_type": "text",
            "text": text,
            "link": {"web_url": link_url, "mobile_web_url": link_url},
            "button_title": "바로가기",
        }
        data = {"template_object": json.dumps(template_obj, ensure_ascii=False)}

        print("[카카오 발송] user:", user.username, "data:", data)

        # 1차 전송
        res = requests.post(KAKAO_MEMO_SEND_URL, headers=_kakao_headers(token.access_token), data=data, timeout=10)
        print("[카카오 응답-1]", res.status_code, res.text)

        result = res.json()

        # 만료/권한 문제면 갱신 후 재시도
        if res.status_code in (401, 403) or result.get("code") == -401:
            print("⚠️ access_token 만료/권한 문제 → 갱신 시도")
            if _refresh_token(token):
                res = requests.post(KAKAO_MEMO_SEND_URL, headers=_kakao_headers(token.access_token), data=data, timeout=10)
                print("[카카오 응답-2]", res.status_code, res.text)
                result = res.json()

        return result
    except Exception as e:
        print("[카카오 알림 오류]", e)
        return {"error": str(e)}

