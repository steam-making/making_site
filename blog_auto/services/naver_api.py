import requests
import json
from django.conf import settings


def publish_to_naver_v3(post):
    """
    네이버 블로그 신형 에디터 Private API 기반 자동 발행
    (JWT token 사용 방식)
    """

    # 1) 로그인 쿠키 준비
    cookies = {
        "NID_AUT": settings.NAVER_COOKIE_NID_AUT,
        "NID_SES": settings.NAVER_COOKIE_NID_SES,
    }

    # 2) JWT 토큰 가져오기
    options_url = f"https://blog.naver.com/PostWriteFormSeOptions.naver?blogId={settings.NAVER_BLOG_NAME}"
    opt_res = requests.get(options_url, cookies=cookies)
    opt_res.raise_for_status()

    token = opt_res.json()["result"]["token"]

    # 3) 글 발행 요청
    publish_url = "https://blog.naver.com/PostWriteAsync.naver"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "title": post.main_title,
        "contents": post.content,
        "categoryNo": None,     # 카테고리 필요하면 번호 매핑 가능
        "directorySeq": 0,
        "imageInfos": [],
        "noticePost": False
    }

    res = requests.post(publish_url, headers=headers, cookies=cookies, data=json.dumps(payload))
    res.raise_for_status()

    result = res.json()
    post_no = result["postNo"]

    return f"https://blog.naver.com/{settings.NAVER_BLOG_NAME}/{post_no}"
