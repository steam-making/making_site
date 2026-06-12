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

    # 지도사과정 과정 유형 관리
    path("instructor/courses/", views.instructor_course_list, name="instructor_course_list"),
    path("instructor/courses/add/", views.instructor_course_add, name="instructor_course_add"),
    path("instructor/courses/<int:pk>/edit/", views.instructor_course_edit, name="instructor_course_edit"),
    path("instructor/courses/<int:pk>/delete/", views.instructor_course_delete, name="instructor_course_delete"),
    path("instructor/courses/<int:pk>/api/", views.course_type_api, name="course_type_api"),

    # 지도사과정 모집 공고 관리
    path("instructor/", views.instructor_recruit, name="instructor_recruit"),
    path("instructor/add/", views.instructor_recruit_add, name="instructor_recruit_add"),
    path("instructor/<int:pk>/edit/", views.instructor_recruit_edit, name="instructor_recruit_edit"),
    path("instructor/<int:pk>/delete/", views.instructor_recruit_delete, name="instructor_recruit_delete"),
    path("instructor/<int:pk>/apply/", views.instructor_recruit_apply, name="instructor_recruit_apply"),
    path("instructor/<int:pk>/applications/", views.instructor_recruit_applications, name="instructor_recruit_applications"),
]
