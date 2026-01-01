from django.urls import path
from . import views

app_name = "progress"

urlpatterns = [
    path("", views.progress_home, name="home"),

    # 관리자/강사
    path("<int:program_id>/lessons/", views.lesson_list, name="lesson_list"),
    path("<int:program_id>/lessons/add/", views.lesson_create, name="lesson_create"),
    path("<int:program_id>/lessons/upload/", views.upload_lessons, name="upload_lessons"),

    # 학생
    path("<int:program_id>/student/", views.student_progress, name="student_progress"),
]
