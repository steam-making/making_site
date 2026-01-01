from django.contrib import admin
from .models import Material, Vendor, VendorType, MaterialOrder, MaterialOrderItem
from .models import MaterialRelease, MaterialReleaseItem, ReleasePaymentStatus


admin.site.register(Vendor)
admin.site.register(VendorType)


class MaterialReleaseItemInline(admin.TabularInline):
    model = MaterialReleaseItem
    extra = 0


@admin.register(MaterialRelease)
class MaterialReleaseAdmin(admin.ModelAdmin):
    list_display = [
        'teacher_name',         # 주문자 이름
        'teacher',              # 주문자 ID
        'institution',
        'order_month',
        'created_by_info',      # ✅ 작성자 정보 (ID + 이름)
        'created_at',
    ]
    list_filter = ['order_month', 'teacher', 'release_date']
    inlines = [MaterialReleaseItemInline]

    def teacher_name(self, obj):
        return obj.teacher.first_name if obj.teacher else '-'
    teacher_name.short_description = '주문자'

    # ✅ 작성자 ID + 이름 표시
    def created_by_info(self, obj):
        """
        관리자(Admin)에서 작성자 정보 표시:
        - 작성자가 있으면 '이메일(ID)\n이름' 두 줄 표시
        - 없으면 '-'
        """
        if obj.created_by:
            name = obj.created_by.first_name or '-'
            return f"{obj.created_by.username}\n{name}"
        return "-"

    created_by_info.short_description = "작성자(ID / 이름)"
    created_by_info.allow_tags = True   # HTML 표시 허용 (필요 시)


class MaterialOrderItemInline(admin.TabularInline):
    model = MaterialOrderItem
    extra = 0


@admin.register(MaterialOrder)
class MaterialOrderAdmin(admin.ModelAdmin):
    list_display = ['teacher_name', 'ordered_date', 'expected_date', 'created_at']
    list_filter = ['ordered_date', 'expected_date']
    search_fields = ['teacher__first_name', 'teacher__username']
    inlines = [MaterialOrderItemInline]

    def teacher_name(self, obj):
        return f"{obj.teacher.first_name} ({obj.teacher.username})" if obj.teacher else '-'
    teacher_name.short_description = '주문자'


@admin.register(ReleasePaymentStatus)
class ReleasePaymentStatusAdmin(admin.ModelAdmin):
    list_display = ['institution', 'order_month', 'status']
    list_filter = ['order_month', 'status', 'institution']


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor", "vendor_type", "supply_price", "stock", "vendor_order")
    list_editable = ("vendor_order",)   # ✅ 관리자 화면에서 바로 수정 가능
    list_filter = ("vendor__vendor_type",)

    class Meta:
        ordering = ["vendor__vendor_type__name", "vendor__name", "vendor_order", "name"]
