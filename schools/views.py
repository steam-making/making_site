import pandas as pd
from django.shortcuts import render
from .models import School
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
from django.contrib import messages
from schools.models import School
from django.core.management import call_command
from django.http import JsonResponse
from .models import School

def school_detail_api(request, pk):
    school = School.objects.get(pk=pk)
    return JsonResponse({
        "id": school.id,
        "name": school.name,
        "address": school.address,
    })

def upload_school_excel(request):
    if request.method == "POST":
        file = request.FILES["file"]
        df = pd.read_excel(file)

        for _, row in df.iterrows():
            school_name = str(row.get("학교명", "")).strip()
            if not school_name:
                continue  # 학교명이 없으면 skip

            # 기존 학교 가져오기 또는 새로 생성
            school, created = School.objects.get_or_create(name=school_name)

            # 업데이트할 값들 준비
            new_values = {
                "student_count": row.get("학생수(계)", ""),
                "homepage": row.get("홈페이지", ""),
                "zipcode": row.get("우편번호", ""),
                "address": row.get("주소", ""),
                "office_phone": row.get("교무실연락처", ""),
            }

            # 빈 값("") 은 업데이트하지 않음 → 기존 값 유지
            for field, value in new_values.items():
                if value not in [None, ""]:     # 비어있지 않은 경우만
                    setattr(school, field, value)

            school.save()

        return render(request, "schools/upload_success.html")

    return render(request, "schools/upload_form.html")


def school_search(request):
    query = request.GET.get("q", "")
    results = []

    if query:
        qs = School.objects.filter(name__icontains=query)[:20]
        for s in qs:
            results.append({
                "id": s.id,
                "name": s.name,
                "student_count": s.student_count,
                "address": s.address,
                "homepage": s.homepage,
                "zipcode": s.zipcode,
                "office_phone": s.office_phone,
            })

    return JsonResponse(results, safe=False)

    

from django.shortcuts import render, redirect, get_object_or_404
from .models import School
from .forms import SchoolForm

def school_create(request):
    if request.method == "POST":
        form = SchoolForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("school_list")
    else:
        form = SchoolForm()
    return render(request, "schools/school_form.html", {"form": form, "mode": "create"})


def school_edit(request, pk):
    school = get_object_or_404(School, pk=pk)

    if request.method == "POST":
        form = SchoolForm(request.POST, instance=school)
        if form.is_valid():
            form.save()
            return redirect("school_list")
    else:
        form = SchoolForm(instance=school)

    return render(request, "schools/school_form.html", {"form": form, "mode": "edit"})

def school_list(request):
    schools = School.objects.all()

    # 주소 기반 지역별 학교 수 계산
    gwangju_count = schools.filter(address__icontains="광주").count()
    jeonnam_count = schools.filter(address__icontains="전라남도").count()
    jeonbuk_count = schools.filter(address__icontains="전라북도").count()

    context = {
        "schools": schools,
        "gwangju_count": gwangju_count,
        "jeonnam_count": jeonnam_count,
        "jeonbuk_count": jeonbuk_count,
    }
    return render(request, "schools/school_list.html", context)



def school_delete(request, pk):
    school = get_object_or_404(School, pk=pk)
    school.delete()
    return redirect("school_list")

from django.http import JsonResponse
from .models import School


@staff_member_required
def school_delete_all(request):
    School.objects.all().delete()
    messages.success(request, "전체 학교 데이터가 삭제되었습니다.")
    return redirect("school_list")


@staff_member_required    # ⭐ 관리자만 실행 가능
def update_schoolinfo(request):
    try:
        call_command("update_schools_schoolinfo")
        messages.success(request, "학교 정보 업데이트가 완료되었습니다!")
    except Exception as e:
        messages.error(request, f"업데이트 중 오류 발생: {e}")

    return redirect("school_list")