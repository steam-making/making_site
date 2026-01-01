from django.contrib import admin
from .models import Notice

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "audience", "status", "is_pinned", "published_at", "view_count")
    list_filter = ("audience", "status", "is_pinned")
    search_fields = ("title", "content")
    ordering = ("-is_pinned", "-published_at")
