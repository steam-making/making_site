from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('list/', views.student_list, name='student_list'),
    path('detail/<int:institution_id>/', views.student_detail, name='student_detail'),
    path('upload/', views.student_upload, name='student_upload'),
    path('template/', views.student_template, name='student_template'),
    
    # ✅ CRUD
    path('<int:institution_id>/add/', views.student_create, name='student_create'),
    path('edit/<int:student_id>/', views.student_update, name='student_update'),
    path('delete/<int:student_id>/', views.student_delete, name='student_delete'),
    path("<int:institution_id>/reset/", views.student_reset, name="student_reset"),

    path("students/move/", views.student_bulk_move, name="student_bulk_move"),

]
