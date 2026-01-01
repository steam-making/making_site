from django.contrib import admin
from django.utils.html import format_html
from .models import DynamicLink

@admin.register(DynamicLink)
class DynamicLinkAdmin(admin.ModelAdmin):
    list_display = ('key', 'url', 'updated_at', 'qr_preview')

    def qr_preview(self, obj):
        qr_url = f"/q/{obj.key}/qr/"
        return format_html(
            '<a href="{}" target="_blank">'
            '<img src="{}" width="80" height="80" style="border:1px solid #ccc;" />'
            '</a>',
            qr_url, qr_url
        )
    qr_preview.short_description = "QR 코드"