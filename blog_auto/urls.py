# blog_auto/urls.py
from django.urls import path
from . import views

app_name = "blog_auto"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("generate/", views.generate_post, name="generate_post"),
    path("<int:post_id>/preview/", views.preview_post, name="preview"),
    path("<int:post_id>/publish/", views.publish_now, name="publish_now"),
]
