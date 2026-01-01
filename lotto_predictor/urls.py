from django.urls import path
from . import views

urlpatterns = [
    path("recommend/", views.lotto_recommend, name="lotto_recommend"),
    path("recommend/save/", views.save_recommendations, name="save_recommendations"),
    path("saved/", views.lotto_saved, name="lotto_saved"),
    path("saved/delete/<int:pk>/", views.delete_recommendation, name="delete_recommendation"),
    path("saved/delete/by-draw/<int:draw_no>/", views.delete_recommendations_by_draw, name="delete_recommendations_by_draw"),
    path("backtest/recent60/", views.lotto_backtest_recent60, name="lotto_backtest_recent60"),

]
