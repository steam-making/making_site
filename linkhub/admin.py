from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import redirect
from django.utils.html import format_html

from .models import NeulbomConfig, SourceSite, CollectedPost
from .services import collect_posts


@admin.register(SourceSite)
class SourceSiteAdmin(admin.ModelAdmin):
    list_display = ("name", "collector", "request_method", "active")
    list_filter = ("collector", "active")
    list_editable = ("collector",)

    # 🔥 목록에 보이는 수집 버튼
    def collect_button(self, obj):
        return format_html(
            '<a class="button" href="collect/{}/">수집</a>',
            obj.id
        )
    collect_button.short_description = "수집 실행"

    # 🔥 관리자 URL 추가
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "collect/<int:site_id>/",
                self.admin_site.admin_view(self.collect_view),
                name="linkhub_collect",
            ),
        ]
        return custom_urls + urls

    # 🔥 실제 수집 처리
    def collect_view(self, request, site_id):
        site = SourceSite.objects.get(id=site_id)
        collect_posts(site)
        messages.success(request, f"'{site.name}' 수집이 완료되었습니다.")
        return redirect("../..")


@admin.register(CollectedPost)
class CollectedPostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "region",
        "school_name",
        "status",        # 🔥
        "post_date",
        "is_new",
        "collected_at",
    )
    list_filter = ("status", "region", "is_new")

@admin.register(NeulbomConfig)
class NeulbomConfigAdmin(admin.ModelAdmin):
    list_display = ("cutoff_date", "updated_at")