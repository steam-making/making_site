from datetime import datetime, date
from django.shortcuts import get_object_or_404, render, redirect
from .models import RecruitNotice
from schools.models import School
from teachers.models import TeachingInstitution
from django.contrib.auth.decorators import login_required

from datetime import date
from django.utils.timezone import localtime
from teachers.models import TeachingInstitution

# =========================
# 🔧 프로그램명 → 핵심 키워드 추출 함수
# =========================
import re

CORE_KEYWORDS = [
    "3d펜",
    "로봇",
    "코딩",
    "ai",
    "메이커",
    "과학",
    "드론",
]

def extract_keywords(text):
    if not text:
        return []

    text = text.lower()

    # 괄호 제거 (요일 등)
    text = re.sub(r"\([^)]*\)", "", text)

    # 공백 정리
    text = re.sub(r"[^가-힣a-z0-9]", " ", text)

    words = text.split()

    keywords = set()

    # ⭐⭐⭐ 핵심 규칙 1: 3d + 펜 계열 강제 통합
    joined = "".join(words)
    if "3d" in joined and "펜" in joined:
        keywords.add("3d펜")

    # ⭐ 핵심 키워드 포함 검사
    for w in words:
        for core in CORE_KEYWORDS:
            if core in w:
                keywords.add(core)

        # 일반 단어도 보조적으로 유지
        if len(w) >= 2:
            keywords.add(w)

    result = list(keywords)
    #print("extract:", text, "→", result)
    return result





@login_required
def recruit_copy(request, pk):
    notice = get_object_or_404(RecruitNotice, pk=pk)

    initial_data = {
        "receive_date": notice.receive_date.strftime("%Y-%m-%d"),
        "deadline": localtime(notice.deadline).strftime("%Y-%m-%dT%H:%M"),
        "region": notice.region,
        "student_count": notice.student_count,
        "school": notice.school.id if notice.school else "",
        "programs": notice.programs or [],
        "attachment_urls": "\n".join(notice.attachment_urls or []),
    }

    SUBMIT_METHOD_OPTIONS = ["늘봄허브", "방문", "우편", "메일"]

    return render(request, "recruit/recruit_form.html", {
        "copy_mode": True,
        "initial": initial_data,
        "submit_method_options": SUBMIT_METHOD_OPTIONS,
        # ⭐ 핵심
        "selected_submit_methods": notice.submit_method.split(", "),
    })


from datetime import date
from teachers.models import TeachingInstitution

# =========================
# 📄 모집공고 리스트
# =========================
def recruit_list(request):
    today = date.today()

    # =========================
    # school 미리 로딩
    # =========================
    notices = RecruitNotice.objects.select_related("school").all()

    for n in notices:
        # =========================
        # ⭐ 상태 자동 계산
        # =========================
        days_left = (n.deadline.date() - today).days

        if 0 <= days_left <= 2 and today <= n.deadline.date():
            n.computed_status = "마감임박"
            n.order_status = 1
        elif n.receive_date <= today <= n.deadline.date():
            n.computed_status = "진행"
            n.order_status = 2
        elif today < n.receive_date:
            n.computed_status = "대기"
            n.order_status = 3
        else:
            n.computed_status = "마감"
            n.order_status = 4

        # =========================
        # ⭐ 제출방법 split (템플릿용)
        # =========================
        n.submit_method_list = (
            [m.strip() for m in n.submit_method.split(",")]
            if n.submit_method else []
        )

        # =========================
        # ⭐⭐ 우리강사 출강 프로그램 판별
        # =========================
        if n.school:
            our_program_names = list(
                TeachingInstitution.objects.filter(
                    school=n.school
                ).values_list("program", flat=True)
            )
        else:
            our_program_names = []

        checked_programs = []

        for p in n.programs or []:
            recruit_keywords = set(
                extract_keywords(p.get("name", ""))
            )

            is_our_program = False

            for our_prog in our_program_names:
                our_keywords = set(
                    extract_keywords(our_prog)
                )

                # ⭐ 키워드 교집합 하나라도 있으면 매칭
                if recruit_keywords & our_keywords:
                    is_our_program = True
                    break

            p["is_our_program"] = is_our_program
            checked_programs.append(p)

        n.checked_programs = checked_programs

    # =========================
    # ⭐ 필터 적용
    # =========================
    status = request.GET.get("status")
    region = request.GET.get("region")
    program = request.GET.get("program")
    school = request.GET.get("school")   # ⭐ 추가

    if status:
        notices = [
            n for n in notices
            if n.computed_status == status
        ]

    if region:
        notices = [
            n for n in notices
            if region.lower() in (n.region or "").lower()
        ]

    # ⭐ 학교명 검색 필터
    if school:
        notices = [
            n for n in notices
            if n.school and school.lower() in n.school.name.lower()
        ]

    if program:
        notices = [
            n for n in notices
            if any(
                program.lower() in p["name"].lower()
                for p in n.programs or []
            )
        ]

    # =========================
    # ⭐ 정렬: 마감임박 → 진행 → 대기 → 마감, 최신순
    # =========================
    notices = sorted(
        notices,
        key=lambda x: (x.order_status, -x.id)
    )

    return render(request, "recruit/recruit_list.html", {
        "notices": notices,
    })



from datetime import datetime, date
from django.shortcuts import render, redirect
from schools.models import School
from .models import RecruitNotice


from datetime import datetime, date
from django.shortcuts import render, redirect
from schools.models import School
from .models import RecruitNotice



def recruit_add(request):
    print("POST:", request.POST)

    submit_method_options = ["늘봄허브", "방문", "우편", "메일"]

    if request.method == "POST":

        # ======================
        # 학교 정보
        # ======================
        school_id = request.POST.get("school")
        school = School.objects.filter(id=school_id).first()

        # ⭐ 우리 강사 출강 학교 자동 판별
        is_our_school = False
        if school:
            is_our_school = TeachingInstitution.objects.filter(
                school=school
            ).exists()

        # ======================
        # 날짜 변환
        # ======================
        receive_date = datetime.strptime(
            request.POST["receive_date"], "%Y-%m-%d"
        ).date()
        deadline = datetime.strptime(
            request.POST["deadline"], "%Y-%m-%dT%H:%M"
        )
        today = date.today()

        # 상태 계산
        if today < receive_date:
            status = "예정"
        elif today > deadline.date():
            status = "마감"
        else:
            status = "모집중"

        # ======================
        # 제출방법 (다중)
        # ======================
        submit_methods = ", ".join(
            request.POST.getlist("submit_method")
        )

        # ======================
        # 첨부파일 링크
        # ======================
        urls_raw = request.POST.get("attachment_urls", "").strip()
        attachment_list = [
            u.strip() for u in urls_raw.split("\n") if u.strip()
        ]

        # ======================
        # 모집 프로그램 여러 개
        # ======================
        program_names = request.POST.getlist("program_name[]")
        program_mng_nos = request.POST.getlist("program_mng_no[]")
        program_fees = request.POST.getlist("program_fee[]")

        programs_list = []
        for name, mng_no, fee in zip(
            program_names, program_mng_nos, program_fees
        ):
            if name.strip() and mng_no.strip():
                programs_list.append({
                    "name": name.strip(),
                    "mng_no": mng_no.strip(),
                    "fee": fee.strip(),
                })

        # ======================
        # DB 저장
        # ======================
        RecruitNotice.objects.create(
            status=status,
            receive_date=receive_date,
            deadline=deadline,
            submit_method=submit_methods,
            region=request.POST["region"],
            school=school,
            student_count=request.POST.get("student_count", ""),
            programs=programs_list,
            attachment_urls=attachment_list,
            is_our_school=is_our_school,   # ⭐ 핵심 추가
        )

        return redirect("recruit_list")

    # GET 요청 → 등록 폼
    return render(request, "recruit/recruit_form.html", {
        "submit_method_options": submit_method_options,
    })



from datetime import datetime, date
from django.shortcuts import render, get_object_or_404, redirect
from schools.models import School
from teachers.models import TeachingInstitution
from .models import RecruitNotice


def recruit_edit(request, pk):
    notice = get_object_or_404(RecruitNotice, pk=pk)

    if request.method == "POST":
        # ================= 학교 =================
        school_id = request.POST.get("school")
        school = School.objects.filter(id=school_id).first()

        # ================= 날짜 =================
        receive_date = datetime.strptime(
            request.POST["receive_date"], "%Y-%m-%d"
        ).date()
        deadline = datetime.strptime(
            request.POST["deadline"], "%Y-%m-%dT%H:%M"
        )
        today = date.today()

        # ================= 상태 자동 계산 =================
        if today < receive_date:
            status = "대기"
        elif today > deadline.date():
            status = "마감"
        else:
            status = "진행"

        # ================= 제출방법 =================
        submit_methods = ", ".join(request.POST.getlist("submit_method"))

        # ================= 첨부파일 =================
        urls_raw = request.POST.get("attachment_urls", "").strip()
        attachment_list = [
            u.strip() for u in urls_raw.split("\n") if u.strip()
        ]

        # ================= 모집 프로그램 =================
        program_names = request.POST.getlist("program_name[]")
        program_mng_nos = request.POST.getlist("program_mng_no[]")
        program_fees = request.POST.getlist("program_fee[]")

        programs_list = []
        for name, mng_no, fee in zip(program_names, program_mng_nos, program_fees):
            if name.strip() and mng_no.strip():
                programs_list.append({
                    "name": name.strip(),
                    "mng_no": mng_no.strip(),
                    "fee": fee.strip(),
                })

        # ================= 🔥 우리 강사 출강 학교 자동 판별 =================
        is_our_school = False
        if school:
            is_our_school = TeachingInstitution.objects.filter(
                school=school
            ).exists()

        # ================= 저장 =================
        notice.status = status
        notice.receive_date = receive_date
        notice.deadline = deadline
        notice.submit_method = submit_methods
        notice.region = request.POST["region"]
        notice.school = school
        notice.student_count = request.POST["student_count"]
        notice.programs = programs_list
        notice.attachment_urls = attachment_list

        # ⭐ 핵심 추가
        notice.is_our_school = is_our_school

        notice.save()

        return redirect("recruit_list")

    submit_method_options = ["늘봄허브", "방문", "우편", "메일"]

    return render(request, "recruit/recruit_edit.html", {
        "notice": notice,
        "submit_method_options": submit_method_options,
    })

  

def recruit_delete(request, pk):
    notice = get_object_or_404(RecruitNotice, pk=pk)
    notice.delete()
    return redirect("recruit_list")


from django.http import JsonResponse


# def school_search(request):
#     q = request.GET.get("q", "")
#     schools = School.objects.filter(name__icontains=q)[:20]

#     data = []
#     for s in schools:
#         data.append({
#             "id": s.id,
#             "name": s.name,
#             "address": s.address,
#             "student_count": s.student_count,
#             # ⭐ 우리 강사 출강 학교 여부
#             "is_our_school": TeacherSchool.objects.filter(school=s).exists(),
#         })

#     return JsonResponse(data, safe=False)
from django.shortcuts import render
from django.db.models import Count, Q
from courses.models import ProgramClass

# =========================
# 요일 / 색상 설정
# =========================
DAY_ORDER = ["mon", "tue", "wed", "thu", "fri", "sat"]
DAY_LABELS = {
    "mon": "월",
    "tue": "화",
    "wed": "수",
    "thu": "목",
    "fri": "금",
    "sat": "토",
}

COLOR_CLASSES = [
    "bg-primary text-white",
    "bg-success text-white",
    "bg-warning text-dark",
    "bg-info text-dark",
    "bg-danger text-white",
    "bg-secondary text-white",
]

def get_color_class(program_id):
    return COLOR_CLASSES[program_id % len(COLOR_CLASSES)]


def recruit_timetable(request):
    classes = (
        ProgramClass.objects
        .select_related("program")
        .annotate(
            current_count=Count(
                "enrollments",
                filter=Q(enrollments__is_active=True)
            )
        )
        .order_by("start_time")
    )

    # ⏰ 시간대 수집 (시작 시간 기준)
    time_slots = sorted({c.start_time for c in classes})

    rows = []
    for t in time_slots:
        # 🔹 해당 시간대의 최대 종료시간 (행 표시용)
        end_times = [c.end_time for c in classes if c.start_time == t]
        time_end = max(end_times) if end_times else None

        row = {
            "time": t,
            "time_end": time_end,
            "cells": []
        }

        for day in DAY_ORDER:
            cell_items = []

            for cls in classes:
                if cls.start_time == t and day in cls.days:
                    cell_items.append({
                        "program_id": cls.program.id,          # 🔥 추가
                        "program_name": cls.program.name,
                        "class_name": cls.name,
                        "start_time": cls.start_time,
                        "end_time": cls.end_time,
                        "current_count": cls.current_count,
                        "capacity": cls.capacity,
                        "color_class": get_color_class(cls.program.id),
                    })


            row["cells"].append({
                "day": day,
                "label": DAY_LABELS[day],
                "items": cell_items
            })

        rows.append(row)

    return render(request, "recruit/recruit_timetable.html", {
        "rows": rows,
        "days": [(d, DAY_LABELS[d]) for d in DAY_ORDER],
    })

