from django.urls import path
from .views import collect_receive_api

urlpatterns = [
    path("collect/receive/", collect_receive_api, name="collect_receive_api"),
]
