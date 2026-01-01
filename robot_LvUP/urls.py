from django.urls import path
from . import views

urlpatterns = [
    path('', views.levelup_institution_list, name='levelup_institution_list'),
    path('<int:institution_id>/', views.levelup_by_institution, name='robot_levelup_by_institution'),
    path('<int:institution_id>/add/', views.levelup_create, name='robot_levelup_create'),
    path('edit/<int:pk>/', views.robot_levelup_update, name='robot_levelup_update'),
    path('delete/<int:pk>/', views.robot_levelup_delete, name='robot_levelup_delete'),
    path('toggle/<int:pk>/<str:field>/', views.toggle_status, name='toggle_status'),
    path('dashboard/', views.levelup_dashboard, name='levelup_dashboard'),
    path('<int:institution_id>/release_auto/<str:year_month>/',views.auto_release_from_levelup,name='auto_release_from_levelup'),
    path('<int:institution_id>/release_preview/<str:year_month>/',views.release_preview,name='release_preview'),
    path('<int:institution_id>/release_confirm/<str:year_month>/',views.release_confirm,name='release_confirm'),

]
