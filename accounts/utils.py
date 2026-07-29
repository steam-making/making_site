# accounts/utils.py
import requests, json
from django.conf import settings
from django.utils import timezone
from accounts.models import KakaoToken

KAKAO_MEMO_SEND_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"

def get_korean_initials(name: str) -> str:
    """
    한글 이름 → 영문 이니셜 (학생 계정용, 안정화 버전)
    예:
      박서준 → psj
      박서율 → psy
      이서준 → ysj
    """

    CHO = [
        "g",   # ㄱ
        "kk",  # ㄲ
        "n",   # ㄴ
        "d",   # ㄷ
        "tt",  # ㄸ
        "r",   # ㄹ
        "m",   # ㅁ
        "p",   # ㅂ
        "pp",  # ㅃ
        "s",   # ㅅ
        "ss",  # ㅆ
        "",    # ㅇ (무음 처리, 첫 글자만 별도 보정)
        "j",   # ㅈ
        "jj",  # ㅉ
        "ch",  # ㅊ
        "k",   # ㅋ
        "t",   # ㅌ
        "p",   # ㅍ
        "h",   # ㅎ
    ]


    result = []

    for idx, char in enumerate(name):
        if "가" <= char <= "힣":
            code = ord(char) - 0xAC00
            cho = code // 588
            initial = CHO[cho]

            # ⭐ 핵심 보정
            if initial == "":
                # 이름 첫 글자의 ㅇ → y
                if idx == 0:
                    result.append("y")
                # 그 외 ㅇ은 생략
            else:
                result.append(initial)

        elif char.isalpha():
            result.append(char.lower())

    return "".join(result)


# -------------------------------------------------
# 학생용 username 생성 (중복 체크 포함)
# psj210427@steam-making.com
# psj210427_2@steam-making.com
# -------------------------------------------------
def generate_unique_student_username(child):
    initials = get_korean_initials(child.name)
    birth = child.birth_date.strftime("%y%m%d")

    base = f"{initials}{birth}"
    domain = "@steam-making.com"

    username = f"{base}{domain}"
    idx = 1

    while User.objects.filter(username=username).exists():
        idx += 1
        username = f"{base}_{idx}{domain}"

    return username


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

def send_kakao_message(user, text, local_test=False, link_url=None):
    """나에게 보내기 (기존 유지)"""
    try:
        token = KakaoToken.objects.filter(user=user).order_by("-created_at").first()
        if not token:
            return {"error": "no_token"}

        if not link_url:
            link_url = "http://127.0.0.1:8000" if local_test else "http://133.186.144.151"
        template_obj = {
            "object_type": "text",
            "text": text,
            "link": {"web_url": link_url, "mobile_web_url": link_url},
            "button_title": "바로가기",
        }
        data = {"template_object": json.dumps(template_obj, ensure_ascii=False)}

        res = requests.post(KAKAO_MEMO_SEND_URL, headers=_kakao_headers(token.access_token), data=data, timeout=10)
        result = res.json()

        if res.status_code in (401, 403) or result.get("code") == -401:
            if _refresh_token(token):
                res = requests.post(KAKAO_MEMO_SEND_URL, headers=_kakao_headers(token.access_token), data=data, timeout=10)
                result = res.json()
        return result
    except Exception as e:
        print("[카카오 나에게 보내기 오류]", e)
        return {"error": str(e)}

def get_kakao_friends(user):
    """카카오 친구 목록 가져오기"""
    try:
        token = KakaoToken.objects.filter(user=user).order_by("-created_at").first()
        if not token:
            print(f"[get_kakao_friends] {user} has no KakaoToken.")
            return None
        
        url = "https://kapi.kakao.com/v1/api/talk/friends"
        res = requests.get(url, headers=_kakao_headers(token.access_token), timeout=10)
        result = res.json()

        if res.status_code in (401, 403) or result.get("code") == -401:
            print(f"[get_kakao_friends] Token error or expired: {result}. Attempting refresh.")
            if _refresh_token(token):
                res = requests.get(url, headers=_kakao_headers(token.access_token), timeout=10)
                result = res.json()
        
        print(f"[get_kakao_friends API RESPONSE for {user}]: {result}")
        return result.get("elements", [])
    except Exception as e:
        print("[카카오 친구 목록 조회 오류]", e)
        return None

def find_friend_uuid(sender_user, target_kakao_id):
    """친구 목록에서 특정 kakao_id를 가진 친구의 uuid를 찾음"""
    friends = get_kakao_friends(sender_user)
    if not friends:
        print(f"[find_friend_uuid] {sender_user}의 친구 목록이 비어있거나 권한이 없습니다.")
        return None
    
    target_kakao_id_str = str(target_kakao_id)
    for friend in friends:
        # 친구가 앱 사용자여야 id가 존재함
        if str(friend.get("id")) == target_kakao_id_str:
            return friend.get("uuid")
    
    print(f"[find_friend_uuid] 친구 목록에서 {target_kakao_id_str}를 찾을 수 없습니다.")
    return None

def send_kakao_friend_message(sender_user, receiver_uuid, text, local_test=False, link_url=None):
    """친구에게 보내기"""
    try:
        token = KakaoToken.objects.filter(user=sender_user).order_by("-created_at").first()
        if not token:
            return {"error": "no_token"}

        url = "https://kapi.kakao.com/v1/api/talk/friends/message/default/send"
        if not link_url:
            link_url = "http://127.0.0.1:8000" if local_test else "http://133.186.144.151"

        template_obj = {
            "object_type": "text",
            "text": text,
            "link": {"web_url": link_url, "mobile_web_url": link_url},
            "button_title": "바로가기",
        }
        data = {
            "receiver_uuids": json.dumps([receiver_uuid]),
            "template_object": json.dumps(template_obj, ensure_ascii=False)
        }

        res = requests.post(url, headers=_kakao_headers(token.access_token), data=data, timeout=10)
        result = res.json()

        if res.status_code in (401, 403) or result.get("code") == -401:
            if _refresh_token(token):
                res = requests.post(url, headers=_kakao_headers(token.access_token), data=data, timeout=10)
                result = res.json()
        return result
    except Exception as e:
        print("[카카오 친구에게 보내기 오류]", e)
        return {"error": str(e)}


from django.contrib.auth.models import User
from django.db import transaction
from accounts.models import Profile, Child

@transaction.atomic
def create_student_account(child):
    # ✅ 1. 같은 이름 + 생년월일 자녀 중 이미 학생 계정 있는지 확인
    existing_child = (
        Child.objects
        .select_related("student_profile")
        .filter(
            name=child.name,
            birth_date=child.birth_date,
            student_profile__isnull=False
        )
        .first()
    )

    if existing_child:
        # 🔥 현재 child에도 연결해줌 (동기화)
        child.student_profile = existing_child.student_profile
        child.save(update_fields=["student_profile"])
        return existing_child.student_profile

    # ✅ 2. 정말 없을 때만 생성
    username = generate_unique_student_username(child)

    user = User.objects.create_user(
        username=username,
        email=username,
        password="m123456*",
        first_name=child.name.strip()
    )

    profile = Profile.objects.create(
        user=user,
        user_type="student"
    )

    child.student_profile = profile
    child.save(update_fields=["student_profile"])

    return profile
