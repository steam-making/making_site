from django.contrib import admin
from .models import Program, ProgramApplication, Target, ProgramType, ProgramClass
from django.utils.formats import number_format

# ✅ ProgramClass Admin
@admin.register(ProgramClass)
class ProgramClassAdmin(admin.ModelAdmin):
    list_display = ("id", "program", "name", "days", "start_time", "end_time", "start_date", "end_date")
    list_filter = ("program", "days")
    search_fields = ("program__name", "name")
    
@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")
    
@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = (
        "name",  "teacher", "get_target_range", "start_date",
        "session_count", "formatted_tuition", "status", "id", "get_program_types", "material"
    )
    
    class Media:
        js = ("admin/js/tuition_format.js",)
        
    list_filter = ("target_start", "target_end", "status", "program_types",)
    search_fields = ("name", "description")
    
    def get_program_types(self, obj):
        return ", ".join([pt.name for pt in obj.program_types.all()])
    get_program_types.short_description = "프로그램 유형"
    
    def get_target_range(self, obj):
        return obj.get_target_range()
    get_target_range.short_description = "대상"

    def formatted_tuition(self, obj):
        """수업료를 120,000 원 형식으로 표시"""
        return f"{number_format(obj.tuition)} 원"
    formatted_tuition.short_description = "수업료"

# ✅ ProgramApplication Admin
@admin.register(ProgramApplication)
class ProgramApplicationAdmin(admin.ModelAdmin):
    list_display = ("program", "get_applicant_name", "get_phone", "get_child", "status", "applied_at")
    list_filter = ("status", "program__name")
    search_fields = ("applicant__user__username", "applicant__user__first_name", "child__name", "phone")

    # ✅ 신청자명 (Profile.user.first_name)
    def get_applicant_name(self, obj):
        return obj.applicant.user.first_name
    get_applicant_name.short_description = "신청자명(부모/학생)"

    # ✅ 연락처
    def get_phone(self, obj):
        return obj.phone
    get_phone.short_description = "연락처"

    # ✅ 자녀
    def get_child(self, obj):
        return obj.child.name if obj.child else "본인"
    get_child.short_description = "자녀"

from django.contrib import admin
from .models import ProgramProduct, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

@admin.register(ProgramProduct)
class ProgramProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "status", "created_at")
    list_filter = ("category", "status",)
    
@admin.register(ProgramType)
class ProgramTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "order")  # 🔥 order 표시
    list_editable = ("order",)              # 🔥 admin 목록에서 즉시 수정 가능
    ordering = ("order", "id")              # 🔥 항상 order 순으로 나오게


from .models import LearningProgram

@admin.register(LearningProgram)
class LearningProgramAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
