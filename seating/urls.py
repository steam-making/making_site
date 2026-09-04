from django.urls import path

from . import views

app_name = 'seating'

urlpatterns = [
    path('<int:institution_id>/', views.seat_manage, name='seat_manage'),
    path('<int:institution_id>/<int:division_id>/fullscreen/', views.seat_fullscreen, name='seat_fullscreen'),
    path('<int:institution_id>/set-group-grid/', views.set_group_grid, name='set_group_grid'),
    path('<int:institution_id>/set-all-group-seats/', views.set_all_group_seats, name='set_all_group_seats'),
    path('<int:institution_id>/<int:division_id>/priority/', views.set_priority_students, name='set_priority_students'),
    path('<int:institution_id>/<int:division_id>/assign-random/', views.assign_random_seats, name='assign_random_seats'),
    path('swap/', views.swap_seats, name='swap_seats'),
    path('assign-single/', views.assign_single_seat, name='assign_single_seat'),
]
