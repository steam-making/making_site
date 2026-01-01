# teachers/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('institutions/', views.institution_list, name='institution_list'),
    path('institutions/add/', views.add_institution, name='add_institution'),
    path('institutions/<int:pk>/edit/', views.institution_update, name='institution_update'),  # ✅ 수정
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    
    path('certificates/', views.certificate_list, name='certificate_list'),
    path('certificates/new/', views.certificate_create, name='certificate_create'),
    path("certificate/<int:pk>/edit/", views.certificate_update, name="certificate_update"),
    path("certificate/<int:pk>/delete/", views.certificate_delete, name="certificate_delete"),

    path('careers/', views.career_list, name='career_list'),
    path('careers/new/', views.career_create, name='career_create'),
    path("career/<int:pk>/edit/", views.career_update, name="career_update"),
    path("career/<int:pk>/delete/", views.career_delete, name="career_delete"),
    
    path('<int:teacher_id>/careers/', views.teacher_career_list, name='teacher_career_list'),
    path('<int:teacher_id>/certificates/', views.teacher_certificate_list, name='teacher_certificate_list'),
    
]
