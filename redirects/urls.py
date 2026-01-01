from django.urls import path
from . import views

app_name = "redirects"

urlpatterns = [
    path("links/", views.link_list, name="link_list"),
    path("links/new/", views.link_create, name="link_create"),
    path("links/<int:pk>/edit/", views.link_update, name="link_update"),
    path("links/<int:pk>/delete/", views.link_delete, name="link_delete"),
    
    path("qr/<str:key>/download/", views.qr_download, name="qr_download"),
    
    path('<str:key>/', views.dynamic_redirect, name='dynamic_redirect'),
    path('<str:key>/qr/', views.qr_code, name='qr_code'),  # ✅ QR 코드 생성
]
