"""
URL configuration for making_site project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from photobook.views import upload_page, create_photobook
from accounts import views as accounts_views
from accounts.views import kakao_login
from django.conf import settings
from django.conf.urls.static import static
from filebrowser.sites import site

urlpatterns = [
    path("grappelli/", include("grappelli.urls")),  # ✅ grappelli 먼저
    path("admin/filebrowser/", site.urls),          # ✅ filebrowser 경로
    path('admin/', admin.site.urls),
    path('', include('main.urls')),  # main 앱의 URL 포함
    path('accounts/', include('accounts.urls')),  # accounts 앱 URL 포함
    path('accounts/', include('django.contrib.auth.urls')),  # 로그인/로그아웃 URL 추가
    path('materials/', include('materials.urls')),  # ✅ 교구재 관리 URL 추가
    path('photobook/upload/', upload_page, name='upload_page'),
    path('photobook/', create_photobook, name='create_photobook'),
    path('attendance/', include('attendance.urls')),  # ✅ 출결 체크 연결
    path('teachers/', include('teachers.urls')),  # ✅ teachers 앱 URL 연결
    path("notices/", include("notices.urls")),
    path("oauth/kakao/callback/", accounts_views.kakao_callback, name="kakao_callback"),
    path('oauth/kakao/login/', kakao_login, name='kakao_login'),
    path("courses/", include("courses.urls")),
    path("lotto/", include("lotto_predictor.urls")),
    path('q/', include('redirects.urls')),  # ✅ QR Redirect 앱
    path('resources/', include('class_resources.urls')),  
    path('tasks/', include('tasks.urls')),
    path('robot_LvUP/', include('robot_LvUP.urls')),
    path('students/', include('students.urls')),
    path("blog-auto/", include("blog_auto.urls")),
    path('py/', include('pycode.urls')),
    # ✅ 진도관리 앱
    path("progress/", include("progress.urls")),
    path("recruit/", include("recruit.urls")),
    path("schools/", include("schools.urls")),
    path("linkhub/", include("linkhub.urls")),
    path("typing/", include("typing_trainer.urls")),
]  

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)