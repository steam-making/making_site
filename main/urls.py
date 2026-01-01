from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # 홈페이지 URL
    path('making/', views.making_page, name='making_page'),
]
