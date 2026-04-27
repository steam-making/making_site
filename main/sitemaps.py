from django.contrib import sitemaps
from django.urls import reverse
from notices.models import Notice

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
        # 공개된 공지사항만 포함
        return Notice.objects.filter(status='published')

    def lastmod(self, obj):
        return obj.published_at

    def location(self, obj):
        return reverse('notices:detail', args=[obj.pk])

sitemaps_dict = {
    'static': StaticViewSitemap,
    'notices': NoticeSitemap,
}
