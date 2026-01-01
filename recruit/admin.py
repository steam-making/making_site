from django.contrib import admin
from .models import RecruitNotice

@admin.register(RecruitNotice)
class RecruitNoticeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "school",
        "display_programs",   # ← JSON 표시용 메소드
        "region",
        "receive_date",
        "deadline",
    )
    
    list_filter = (
        "status",
        "region",
    )

    search_fields = ("school__name", "region")

    # JSON programs 표시용
    def display_programs(self, obj):
        if not obj.programs:
            return "-"
        return ", ".join([p["name"] for p in obj.programs])

    display_programs.short_description = "모집 프로그램"
