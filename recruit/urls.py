from django.urls import path
from . import views

urlpatterns = [
    path("", views.recruit_list, name="recruit_list"),
    path("add/", views.recruit_add, name="recruit_add"),
    path("<int:pk>/edit/", views.recruit_edit, name="recruit_edit"),
    path("<int:pk>/delete/", views.recruit_delete, name="recruit_delete"),

    # ⭐ 복사
    path("<int:pk>/copy/", views.recruit_copy, name="recruit_copy"),

    path("timetable/", views.recruit_timetable, name="recruit_timetable"),
]
