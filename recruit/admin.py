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

from django.contrib import admin
from .models import RecruitProgram

@admin.register(RecruitProgram)
class RecruitProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "get_day_display", "start_time", "end_time", "capacity")
    list_filter = ("day",)

from .models import InstructorRecruit, InstructorApplication

@admin.register(InstructorRecruit)
class InstructorRecruitAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "recruit_start", "recruit_end", "capacity", "created_at")
    list_filter = ("status",)
    search_fields = ("title",)

@admin.register(InstructorApplication)
class InstructorApplicationAdmin(admin.ModelAdmin):
    list_display = ("applicant_name", "recruit", "phone", "status", "applied_at")
    list_filter = ("status", "recruit")
    search_fields = ("applicant_name", "phone", "recruit__title")

