from django.urls import path, include
from . import views

app_name = "linkhub"

urlpatterns = [
    path("", views.post_hub, name="post_hub"),
    path("gwangju/", views.post_hub_gwangju, name="post_hub_gwangju"),
    path("jeonnam/", views.post_hub_jeonnam, name="post_hub_jeonnam"),

    path("collect/", views.collect_posts_view, name="collect"),
    path("delete-all/", views.collectedpost_delete_all, name="delete_all"),
    # 🔥 SourceSite 관리
    path("sources/", views.source_list, name="source_list"),
    path("sources/add/", views.source_create, name="source_add"),
    path("sources/<int:pk>/edit/", views.source_update, name="source_edit"),
    path("sources/<int:pk>/delete/", views.source_delete, name="source_delete"),

    path("source/<int:pk>/toggle/",views.source_toggle_active,name="source_toggle_active",),
    path("api/", include("linkhub.api_urls")),
    
    path( "neulbom/cutoff/update/", views.neulbom_cutoff_update, name="neulbom_cutoff_update" ),

]
