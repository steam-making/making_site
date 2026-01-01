# teachers/admin.py

from django.contrib import admin
from .models import TeachingInstitution, TeachingDay


@admin.register(TeachingInstitution)
class TeachingInstitutionAdmin(admin.ModelAdmin):
    list_display = ['name', 'program', 'teacher', 'get_days', 'created_at']
    list_filter = ['program', 'teacher']
    search_fields = ['name', 'program', 'teacher__first_name', 'teacher__username']

    def get_days(self, obj):
        return ", ".join(day.code for day in obj.days.all())
    get_days.short_description = "출강 요일"


@admin.register(TeachingDay)
class TeachingDayAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']
