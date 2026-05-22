from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='openbanking_dashboard'),
    path('auth/', views.auth_start, name='openbanking_auth_start'),
    path('auth/callback/', views.auth_callback, name='openbanking_auth_callback'),
    path('accounts/', views.account_list, name='openbanking_accounts'),
    path('transactions/', views.transaction_list, name='openbanking_transactions'),
    path('sync/', views.sync_transactions, name='openbanking_sync'),
    path('match/', views.manual_match, name='openbanking_manual_match'),
    path('unmatch/', views.unmatch_transaction, name='openbanking_unmatch'),
]
