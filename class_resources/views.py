from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

# ✅ 관리자 또는 강사만 접근 허용
def is_staff_or_teacher(user):
    return user.is_staff or getattr(user.profile, 'user_type', '') == 'center_teacher'

@login_required
@user_passes_test(is_staff_or_teacher)
def resource_list(request):
    """전체 수업자료 메인 페이지"""
    categories = [
        {"slug": "3dpen", "name": "3D펜"},
        {"slug": "robot", "name": "로봇"},
        {"slug": "science", "name": "과학"},
        {"slug": "math", "name": "창의수학"},
        {"slug": "coding", "name": "코딩"},
        {"slug": "drone", "name": "항공드론"},
        {"slug": "career", "name": "진로체험"},
    ]
    return render(request, "class_resources/resource_list.html", {"categories": categories})


@login_required
@user_passes_test(is_staff_or_teacher)
def resource_detail(request, category):
    """각 과목별 상세자료 페이지"""
    template_name = f"class_resources/detail_{category}.html"
    return render(request, template_name, {"category": category})

# ✅ 로봇 세부 페이지
@login_required
@user_passes_test(is_staff_or_teacher)
def robot_olloai(request):
    return render(request, "class_resources/robot/olloai.html")

@login_required
@user_passes_test(is_staff_or_teacher)
def robot_probo(request):
    return render(request, "class_resources/robot/probo.html")

@login_required
@user_passes_test(is_staff_or_teacher)
def robot_xrobo(request):
    return render(request, "class_resources/robot/xrobo.html")

@login_required
@user_passes_test(is_staff_or_teacher)
def robot_jrobo(request):
    return render(request, "class_resources/robot/jrobo.html")