from django.urls import path
from . import views

app_name = "typing_trainer"

urlpatterns = [
    path("", views.home, name="home"),
    path("practice/<int:stage_id>/", views.practice, name="practice"),
    path("practice/<int:stage_id>/save/", views.save_result, name="save_result"),
]
