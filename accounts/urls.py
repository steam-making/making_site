from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import views as auth_views
from .views import signup, profile, change_password, check_username,approve_users,institution_signup
from . import views

urlpatterns = [
    path('signup/', signup, name='signup'),
    path('profile/', profile, name='profile'),  # 마이페이지 URL 추가
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),  # 로그인 뷰
    path('logout/', LogoutView.as_view(), name='logout'),  # 로그아웃 뷰
    path('change-password/', change_password, name='change_password'),  # 비밀번호 변경 페이지
    path('check-username/', check_username, name='check_username'),  # ✅ 추가
    path('approve_users/', approve_users, name='approve_users'), #관리자 승인 페이지
    path('redirect/', views.redirect_after_login, name='redirect_after_login'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('members/', views.admin_user_list, name='admin_user_list'),
    path("withdrawal/", views.request_withdrawal, name="request_withdrawal"), #회원탈퇴
    
    path('parents/dashboard/', views.parent_dashboard, name='parent_dashboard'),   # ✅ 학부모 대시보드
    path('parents/children/', views.child_list, name='child_list'),               # ✅ 자녀 관리
    path("parents/children/<int:pk>/edit/", views.child_edit, name="child_edit"),
    path("parents/children/<int:pk>/delete/", views.child_delete, name="child_delete"),
    path('signup/institution/', institution_signup, name='institution_signup'),
    
    # ✅ 비밀번호 재설정
    path("password_reset/", auth_views.PasswordResetView.as_view(template_name="registration/password_reset_form.html"),name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"),name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"), name="password_reset_confirm"),
    path("reset/done/",auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"), name="password_reset_complete"),

    path(
        "admin/activate/<int:user_id>/",
        views.admin_user_activate,
        name="admin_user_activate",
    ),

    path(
        "members/bulk-create/",
        views.admin_user_bulk_create,
        name="admin_user_bulk_create",
    ),
]
