from django.contrib import admin
from .models import MenuItem

class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fk_name = 'parent'
    fields = ('title', 'url', 'icon_class', 'order', 'access_level', 'is_active')

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'parent', 'order', 'access_level', 'is_active')
    list_filter = ('access_level', 'is_active', 'parent')
    search_fields = ('title', 'url')
    ordering = ('order',)
    inlines = [MenuItemInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'parent', 'url', 'icon_class')
        }),
        ('설정', {
            'fields': ('order', 'access_level', 'is_active'),
        }),
    )
