from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
import re

from linkhub.models import CollectedPost, NeulbomConfig, SourceSite
from linkhub.services import collect_posts


class Command(BaseCommand):
    help = "매일 오전 8시 linkhub 수집 + 마감 3일 초과 자동삭제"

    def handle(self, *args, **kwargs):
        today = date.today()
        yesterday = today - timedelta(days=1)

        # 1. 수집 기준일을 어제로 자동 설정
        config, _ = NeulbomConfig.objects.get_or_create(
            pk=1,
            defaults={"cutoff_date": yesterday},
        )
        if config.cutoff_date != yesterday:
            config.cutoff_date = yesterday
            config.save(update_fields=["cutoff_date"])
        self.stdout.write(f"[linkhub] 수집 기준일: {yesterday}")

        # 2. 기존 NEW 플래그 초기화
        CollectedPost.objects.filter(is_new=True).update(is_new=False)

        # 3. 광주 + 전남 활성 사이트 수집
        sites = SourceSite.objects.filter(active=True, area__in=["GWANGJU", "JEONNAM"])
        total_new = 0
        for site in sites:
            try:
                count = collect_posts(site)
                total_new += count or 0
                self.stdout.write(f"[linkhub] [{site.area}] {site.name}: {count}건 수집")
            except Exception as e:
                self.stderr.write(f"[linkhub] [{site.area}] {site.name} 수집 오류: {e}")

        self.stdout.write(f"[linkhub] 총 신규 수집: {total_new}건")

        # 4. 마감일 3일 초과 게시물 삭제
        deleted = self._delete_expired_posts(today)
        self.stdout.write(f"[linkhub] 만료 삭제: {deleted}건 (마감 3일 초과)")

    def _delete_expired_posts(self, today):
        cutoff = today - timedelta(days=3)
        to_delete = []

        for post in CollectedPost.objects.filter(post_date__isnull=False).exclude(post_date=""):
            end_date = self._parse_end_date(post.post_date)
            if end_date and end_date < cutoff:
                to_delete.append(post.pk)

        if to_delete:
            deleted_count, _ = CollectedPost.objects.filter(pk__in=to_delete).delete()
            return deleted_count
        return 0

    def _parse_end_date(self, post_date_str):
        dates = re.findall(r"\d{2,4}[.\-]\d{1,2}[.\-]\d{1,2}", post_date_str)
        if len(dates) < 2:
            return None
        try:
            d = dates[1].replace(".", "-")
            parts = d.split("-")
            if len(parts[0]) == 2:
                year = date.today().year
                month, day = int(parts[1]), int(parts[2])
            else:
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            return date(year, month, day)
        except Exception:
            return None
