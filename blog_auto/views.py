# blog_auto/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib import messages

from .models import AutoPost, BlogCategory
from .services.gpt_post_generator import generate_blog_post
from .services.gpt_image_generator import generate_thumbnail_image
from .services.tistory_api import publish_to_tistory
from blog_auto.services.naver_api_selenium import publish_to_naver_selenium


def dashboard(request):
    posts = AutoPost.objects.all()[:50]
    return render(request, "blog_auto/dashboard.html", {
        "posts": posts,
        "categories": BlogCategory.choices,
    })


@require_POST
def generate_post(request):
    topic = request.POST.get("topic")
    category = request.POST.get("category")
    platform = request.POST.get("platform", AutoPost.PLATFORM_BOTH)
    generate_image = request.POST.get("generate_image") == "on"

    cat_label = dict(BlogCategory.choices).get(category, "교육")
    data = generate_blog_post(topic, cat_label)

    titles = data.get("titles", [])
    main_title = titles[0] if titles else topic

    post = AutoPost.objects.create(
        topic=topic,
        category=category,
        platform=platform,
        main_title=main_title,
        alt_titles=titles,
        raw_response=data,
        content=data.get("content", ""),
        keywords=data.get("keywords", []),
        cta=data.get("cta", ""),
        status=AutoPost.STATUS_READY,
    )

    if generate_image:
        img_file = generate_thumbnail_image(topic)
        post.thumbnail.save(img_file.name, img_file, save=True)

    return redirect("blog_auto:preview", post_id=post.id)


def preview_post(request, post_id):
    post = get_object_or_404(AutoPost, id=post_id)
    return render(request, "blog_auto/preview.html", {"post": post})


@require_POST
def publish_now(request, post_id):
    post = get_object_or_404(AutoPost, id=post_id)

    try:
        # 🚀 네이버 자동 발행
        if post.platform in [AutoPost.PLATFORM_NAVER, AutoPost.PLATFORM_BOTH]:
            naver_url = publish_to_naver_selenium(post)
            post.naver_post_id = naver_url

        # 🚀 티스토리 자동 발행
        if post.platform in [AutoPost.PLATFORM_TISTORY, AutoPost.PLATFORM_BOTH]:
            tistory_id = publish_to_tistory(post)
            post.tistory_post_id = tistory_id

        post.status = AutoPost.STATUS_PUBLISHED
        post.published_at = timezone.now()
        post.save()

        messages.success(request, "발행 완료!")

    except Exception as e:
        post.status = AutoPost.STATUS_FAILED
        post.save()
        messages.error(request, f"발행 실패: {e}")
        raise e

    return redirect("blog_auto:dashboard")
