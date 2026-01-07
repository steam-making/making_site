from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, Child,InstitutionProfile

# Profile을 User admin에 인라인으로 연결
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = '프로필 정보'

# 기존 UserAdmin 확장
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

# 기존 User admin을 다시 등록
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class ChildInline(admin.TabularInline):
    model = Child
    fk_name = "parent"   # ⭐ 핵심
    extra = 0


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "user_type", "phone_number", "birth_date")
    list_filter = ("user_type",)
    search_fields = ("user__username", "user__first_name", "phone_number")
    inlines = [ChildInline]   # ✅ 자녀 인라인 연결
    
    def approve_withdrawal(self, request, queryset):
        for profile in queryset.filter(withdrawal_requested=True):
            user = profile.user
            user.delete()  # ✅ 실제 계정 삭제
        self.message_user(request, "선택된 회원들의 탈퇴를 승인했습니다.")
    approve_withdrawal.short_description = "선택된 회원 탈퇴 승인"

@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ("name", "birth_date", "parent")
    search_fields = ("name", "parent__user__username")
    list_filter = ("birth_date",)
    
@admin.register(InstitutionProfile)
class InstitutionProfileAdmin(admin.ModelAdmin):
    list_display = (
        'institution_name',
        'contact_name',
        'office_phone',   # 기관 전화번호
        'contact_phone',  # 담당자 휴대폰
        'business_number',
        'industry',
        'created_at',
    )
    search_fields = ('institution_name', 'contact_name', 'business_number')
    list_filter = ('industry', 'created_at')
