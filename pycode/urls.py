from django.urls import path
from . import views

urlpatterns = [
    path('', views.editor, name='editor'),
    path('run/', views.run_code, name='run_code'),
]