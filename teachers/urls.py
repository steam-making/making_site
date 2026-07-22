# teachers/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('institutions/', views.institution_list, name='institution_list'),
    path('institutions/add/', views.add_institution, name='add_institution'),
    path('institutions/<int:pk>/edit/', views.institution_update, name='institution_update'),  # ✅ 수정
    path('institutions/<int:pk>/delete/', views.institution_delete, name='institution_delete'),
    path('institutions/<int:pk>/close/', views.institution_close, name='institution_close'),
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    
    path('certificates/', views.certificate_list, name='certificate_list'),
    path('certificate-catalog/', views.certificate_catalog, name='certificate_catalog'),
    path('certificate-catalog/acquire/', views.certificate_catalog_acquire, name='certificate_catalog_acquire'),
    path('certificate-catalog/save/', views.certificate_catalog_save, name='certificate_catalog_save'),
    path('certificate-catalog/<int:item_id>/delete/', views.certificate_catalog_delete, name='certificate_catalog_delete'),
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
