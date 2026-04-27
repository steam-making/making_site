from django.contrib import sitemaps
from django.urls import reverse
from notices.models import MultipleNotice

class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return ['main:index', 'notices:list']

    def location(self, item):
        return reverse(item)

class NoticeSitemap(sitemaps.Sitemap):
    priority = 0.6
    changefreq = 'daily'

    def items(self):
        # 공개된 공지사항만 포함 (필요 시 필터 조정)
        return MultipleNotice.objects.all().order_by('-created_at')

    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else obj.created_at

    def location(self, obj):
        return reverse('notices:detail', args=[obj.pk])

sitemaps_dict = {
    'static': StaticViewSitemap,
    'notices': NoticeSitemap,
}
