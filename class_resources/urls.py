from django.urls import path
from . import views

urlpatterns = [
    path('', views.resource_list, name='resource_list'),
    path('<str:category>/', views.resource_detail, name='resource_detail'),
    
    # ✅ 로봇 하위 페이지
    path('robot/olloai/', views.robot_olloai, name='robot_olloai'),
    path('robot/probo/', views.robot_probo, name='robot_probo'),
    path('robot/xrobo/', views.robot_xrobo, name='robot_xrobo'),
    path('robot/jrobo/', views.robot_jrobo, name='robot_jrobo'),
]
