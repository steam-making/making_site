from django.contrib import admin
from .models import TypingStage, TypingResult


@admin.register(TypingStage)
class TypingStageAdmin(admin.ModelAdmin):
    list_display = ("order", "stage_type", "name", "min_speed", "min_accuracy")
    list_display_links = ("name",)   # ✅ 링크는 name 컬럼
    list_editable = ("order",)       # ✅ order는 바로 수정 가능
    ordering = ("order",)



@admin.register(TypingResult)
class TypingResultAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "stage",
        "speed",
        "accuracy",
        "typo_count",
        "passed",
        "created_at",
    )
    list_filter = ("stage__stage_type", "passed")
