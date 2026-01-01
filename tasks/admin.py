from django.contrib import admin
from .models import Task, WorkType

@admin.register(WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    ordering = ['order']
    search_fields = ['name']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'work_type', 'created_by', 'due_date', 'completed']
    list_filter = ['work_type', 'completed']
    search_fields = ['title', 'description']
