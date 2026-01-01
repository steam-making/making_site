from django.urls import path
from . import views

urlpatterns = [
    path("upload/", views.upload_school_excel, name="upload_school_excel"),
    path("search/", views.school_search, name="school_search"),

    path("add/", views.school_create, name="school_add"),
    path("<int:pk>/edit/", views.school_edit, name="school_edit"),
    path("", views.school_list, name="school_list"),

    path("<int:pk>/delete/", views.school_delete, name="school_delete"),

    path("upload/", views.upload_school_excel, name="upload_school_excel"),
    path("delete_all/", views.school_delete_all, name="school_delete_all"),
    path("update/", views.update_schoolinfo, name="update_schoolinfo"),

    path("<int:pk>/detail/", views.school_detail_api),
]
