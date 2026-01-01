# blog_auto/management/commands/auto_publish_blog.py
from django.core.management.base import BaseCommand
from django.utils import timezone

from blog_auto.models import AutoPost
from blog_auto.services.naver_api import publish_to_naver
from blog_auto.services.tistory_api import publish_to_tistory


class Command(BaseCommand):
    help = "예약된 블로그 글을 자동 발행합니다."

    def handle(self, *args, **options):
        now = timezone.now()
        posts = AutoPost.objects.filter(
            status__in=[AutoPost.STATUS_READY, AutoPost.STATUS_SCHEDULED],
            publish_at__lte=now,
        )

        for post in posts:
            self.stdout.write(f"발행 시도: {post.id} - {post.main_title}")
            try:
                if post.platform in [AutoPost.PLATFORM_NAVER, AutoPost.PLATFORM_BOTH]:
                    naver_id = publish_to_naver(post)
                    post.naver_post_id = naver_id

                if post.platform in [AutoPost.PLATFORM_TISTORY, AutoPost.PLATFORM_BOTH]:
                    tistory_id = publish_to_tistory(post)
                    post.tistory_post_id = tistory_id

                post.status = AutoPost.STATUS_PUBLISHED
                post.published_at = now
                post.save()
            except Exception as e:
                post.status = AutoPost.STATUS_FAILED
                post.save()
                self.stderr.write(f"발행 실패: {post.id} / {e}")
