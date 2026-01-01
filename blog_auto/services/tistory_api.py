# blog_auto/services/tistory_api.py
import requests
from django.conf import settings


def publish_to_tistory(post):
    """
    티스토리 Open API로 글 발행
    """
    url = "https://www.tistory.com/apis/post/write"

    contents = post.content
    if post.cta:
        contents += f"\n\n<strong>{post.cta}</strong>"

    # 티스토리는 기본적으로 x-www-form-urlencoded
    params = {
        "access_token": settings.TISTORY_ACCESS_TOKEN,
        "output": "json",
        "blogName": settings.TISTORY_BLOG_NAME,
        "title": post.main_title,
        "content": contents,
        "visibility": 3,  # 3: 발행
        # "category": 0,  # 티스토리 카테고리 ID 있을 경우
        "tag": ",".join(post.keywords) if post.keywords else "",
    }

    res = requests.post(url, data=params)
    res.raise_for_status()
    data = res.json()

    post_id = data["tistory"]["postId"]
    return post_id
