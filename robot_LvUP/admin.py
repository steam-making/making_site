from django.contrib import admin
from .models import RobotLevelUp

@admin.register(RobotLevelUp)
class RobotLevelUpAdmin(admin.ModelAdmin):
    # ✅ Admin 목록에서 보여줄 항목
    list_display = [
        'year_month', 'student_name', 'kit_name', 'institution',
        'price', 'guide_done', 'release_done', 'delivery_done'
    ]

    # ✅ 필터는 실제 DB 필드만 가능
    list_filter = [
        'year_month', 'institution', 'material',
        'guide_done', 'release_done', 'delivery_done'
    ]

    # ✅ 검색 가능 항목
    search_fields = ['student_name', 'institution', 'material__name']

    # ✅ 정렬 기준
    ordering = ['-year_month', 'student_name']

    # ✅ 커스텀 표시용 메서드
    def kit_name(self, obj):
        return obj.material.name if obj.material else "-"
    kit_name.short_description = "교구명"
