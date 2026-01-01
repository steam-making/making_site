from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import date
from .models import RobotLevelUp
from .forms import RobotLevelUpForm
from materials.models import Material, MaterialRelease, MaterialReleaseItem, TeachingInstitution
from students.models import Student   # ✅ 출강장소별 학생정보 추가

def release_preview(request, institution_id, year_month):

    institution = get_object_or_404(TeachingInstitution, id=institution_id)

    records = RobotLevelUp.objects.filter(
        institution_id=institution_id,
        year_month=year_month,
        release_done=False
    )

    # 교구별 수량 집계
    summary = {}
    for r in records:
        m = r.material
        if m.id not in summary:
            summary[m.id] = {
                "material": m,
                "vendor": m.vendor,
                "unit_price": m.school_price,   # 납품가
                "quantity": 0,
                "stock": m.stock,               # ⭐ 센터 재고 추가
            }
        summary[m.id]["quantity"] += 1

    # 합계 계산
    for v in summary.values():
        v["total_price"] = v["unit_price"] * v["quantity"]

    total_sum = sum(v["total_price"] for v in summary.values())

    return render(request, "robot_LvUP/release_preview.html", {
        "institution": institution,
        "year_month": year_month,
        "items": summary.values(),
        "total_sum": total_sum,
    })


def release_confirm(request, institution_id, year_month):
    institution = get_object_or_404(TeachingInstitution, id=institution_id)

    records = RobotLevelUp.objects.filter(
        institution_id=institution_id,
        year_month=year_month,
        release_done=False
    )

    if not records.exists():
        messages.warning(request, f"{year_month} 출고할 단계업 항목이 없습니다.")
        return redirect("robot_levelup_by_institution", institution_id)

    # 출고 마스터 생성
    release = MaterialRelease.objects.create(
        teacher=institution.teacher,
        institution=institution,
        order_month=year_month,
        created_by=request.user,
    )

    # 교구별 집계
    summary = {}
    for r in records:
        m = r.material
        summary[m.id] = summary.get(m.id, 0) + 1

    # 상세 생성 (교구별 출고방법 포함)
    for material_id, qty in summary.items():
        m = Material.objects.get(id=material_id)

        unit_price = m.school_price

        # ⭐ 교구별 출고방법 읽기
        method = request.POST.get(f"method_{material_id}", "택배")

        MaterialReleaseItem.objects.create(
            release=release,
            material=m,
            vendor=m.vendor,
            quantity=qty,
            unit_price=unit_price,
            status="pending",
            release_method=method,   # ⭐ 교구별 적용
        )

    # 단계업 출고완료 처리
    records.update(
        release_done=True,
        release_date=timezone.now().date()
    )

    messages.success(request, f"{year_month} 단계업 출고등록이 완료되었습니다!")
    return redirect("robot_levelup_by_institution", institution_id)



def auto_release_from_levelup(request, institution_id, year_month):

    institution = get_object_or_404(TeachingInstitution, id=institution_id)

    # 해당 기관+해당 year_month+출고 안됐던 단계업
    records = RobotLevelUp.objects.filter(
        institution_id=institution_id,
        year_month=year_month,
        release_done=False
    )

    if not records.exists():
        messages.warning(request, f"{year_month} 출고할 단계업 항목이 없습니다.")
        return redirect("robot_levelup_by_institution", institution_id)

    # ⭐ 교구별 수량 집계
    summary = {}
    for r in records:
        mid = r.material.id
        summary[mid] = summary.get(mid, 0) + 1

    # ⭐ 출고 마스터 생성
    release = MaterialRelease.objects.create(
        teacher=institution.teacher,  # User FK
        institution=institution,
        order_month=year_month,
        created_by=request.user,
    )

    # ⭐ 출고 상세 생성 (MaterialReleaseItem)
    for material_id, qty in summary.items():

        material_obj = Material.objects.get(id=material_id)

        # ⭐ 단가 가져오기 (Material 모델의 필드 이름에 맞춰 조정)
        # school_price / institution_price / supply_price 중 실제 필드 확인 필요
        # 아래는 가장 일반적인 supply_price 기준
        unit_price = material_obj.supply_price if hasattr(material_obj, "supply_price") else 0

        MaterialReleaseItem.objects.create(
            release=release,
            vendor=material_obj.vendor,
            material=material_obj,
            quantity=qty,
            unit_price=unit_price,   # 🔥 단가 입력!
            status="pending",        # 🔥 자동 생성은 출고대기
            release_method="택배",    # 기본 택배
            included=True
        )

    # ⭐ 단계업 출고 완료 처리
    records.update(
        release_done=True,
        release_date=timezone.now().date()
    )

    messages.success(request, f"{year_month} 단계업 기반 출고등록이 완료되었습니다!")
    return redirect("robot_levelup_by_institution", institution_id)


# ✅ 출강장소 리스트
@login_required
def levelup_institution_list(request):
    """출강장소별 단계업 관리 - 출강장소 선택"""
    if request.user.is_staff:
        institutions = TeachingInstitution.objects.all()
    else:
        institutions = TeachingInstitution.objects.filter(teacher=request.user)

    return render(request, 'robot_LvUP/levelup_institution_list.html', {
        'institutions': institutions
    })

from django.db.models import Count, Sum
from collections import OrderedDict
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from .models import RobotLevelUp
from materials.models import TeachingInstitution


@login_required
def levelup_by_institution(request, institution_id):
    """특정 출강장소의 단계업 관리 (월별 그룹 + 통계 포함)"""
    institution = get_object_or_404(TeachingInstitution, id=institution_id)

    if not request.user.is_staff and institution.teacher != request.user:
        return render(request, "403.html", status=403)

    # ✅ 기본 레코드 (정렬 유지)
    records = (
        RobotLevelUp.objects
        .filter(institution=institution)
        .select_related("material")
        .order_by(
            "year_month",           # 년월
            "delivery_done",        # 전달 안된 게 먼저
            "section",
            "grade",
            "class_no",
            "student_no",
            "student_name",
        )
    )

    # =========================================================
    # ✅ 전체 통계
    # =========================================================
    total = records.count()
    total_price = records.aggregate(Sum("price"))["price__sum"] or 0
    guide_done = records.filter(guide_done=True).count()
    release_done = records.filter(release_done=True).count()
    delivery_done = records.filter(delivery_done=True).count()

    # =========================================================
    # ✅ 출고 완료 · 전달 미완료 교구 (전체 요약)
    # =========================================================
    undelivered_materials = (
        records
        .filter(release_done=True, delivery_done=False)
        .values("material__name")
        .annotate(qty=Count("id"))
        .order_by("material__name")
    )
    undelivered_total_qty = sum(m["qty"] for m in undelivered_materials)

    # =========================================================
    # ✅ 월별 그룹핑 + 월별 통계 (완성본)
    # =========================================================
    grouped_records = OrderedDict()
    monthly_stats = OrderedDict()

    for r in records:
        grouped_records.setdefault(r.year_month, []).append(r)

    for ym, items in grouped_records.items():
        total_cnt = len(items)

        guide_cnt = sum(1 for i in items if i.guide_done)
        release_cnt = sum(1 for i in items if i.release_done)
        delivered_cnt = sum(1 for i in items if i.delivery_done)

        # 월별 전달 미완료 교구 집계
        undelivered = {}
        for i in items:
            if i.release_done and not i.delivery_done:
                name = i.material.name
                undelivered[name] = undelivered.get(name, 0) + 1

        monthly_stats[ym] = {
            "total": total_cnt,
            "guide_done": guide_cnt,        # ✅ 추가
            "release_done": release_cnt,    # ✅ 추가
            "delivered": delivered_cnt,
            "undelivered": undelivered,
        }


    # =========================================================
    # ✅ 렌더링
    # =========================================================
    return render(request, "robot_LvUP/robot_levelup_list.html", {
        # 기본
        "institution": institution,
        "records": records,

        # 전체 통계
        "total": total,
        "total_price": total_price,
        "guide_done": guide_done,
        "release_done": release_done,
        "delivery_done": delivery_done,

        # 전체 미전달 요약
        "undelivered_materials": undelivered_materials,
        "undelivered_total_qty": undelivered_total_qty,

        # 🔥 월별 기능 핵심 데이터
        "grouped_records": grouped_records,
        "monthly_stats": monthly_stats,
    })



# ✅ 등록
@login_required
def levelup_create(request, institution_id):
    """출강장소별 단계업 등록"""
    institution = get_object_or_404(TeachingInstitution, id=institution_id)
    if not request.user.is_staff and institution.teacher != request.user:
        return render(request, "403.html", status=403)
    
    # ✅ 출강장소의 division(부서)에 속한 학생들 중 '미수강' 제외
    students = (
        Student.objects
        .filter(division__institution=institution)
        .exclude(division__division__icontains="미수강")
        .order_by("grade", "class_name", "number")
    )

    # ✅ 로봇 교구 목록 
    robot_materials = Material.objects.filter(
        vendor__vendor_type__name__icontains='로봇'
    )

    if request.method == "POST":
        rows = int(request.POST.get("row_count", 1))
        created = 0

        for i in range(1, rows + 1):
            # ✅ form 입력 name과 정확히 일치하도록 수정
            material_id = request.POST.get(f"material_id_{i}")
            section = request.POST.get(f"part_{i}")
            grade = request.POST.get(f"grade_{i}")
            class_no = request.POST.get(f"class_name_{i}")
            student_no = request.POST.get(f"number_{i}")
            student_name = request.POST.get(f"student_name_{i}")
            price = request.POST.get(f"price_{i}") or 0
            note = request.POST.get(f"note_{i}", "")
            year_month = request.POST.get("year_month")

            # ✅ 필수값 확인
            if not (student_name and material_id):
                continue

            # ✅ DB 저장
            RobotLevelUp.objects.create(
                institution=institution,
                year_month=year_month,
                material_id=material_id,
                section=section,
                grade=grade or None,
                class_no=class_no or None,
                student_no=student_no or None,
                student_name=student_name,
                price=price,
                note=note,
            )
            created += 1

        # ✅ 메시지 처리
        if created > 0:
            messages.success(request, f"단계업 등록이 완료되었습니다. (총 {created}건)")
        else:
            messages.warning(request, "등록된 항목이 없습니다. 교구나 학생을 확인하세요.")

        return redirect("robot_levelup_by_institution", institution_id=institution.id)

    return render(request, "robot_LvUP/robot_levelup_form.html", {
        "institution": institution,
        "students": students,
        "robot_materials": robot_materials,
    })


@login_required
def robot_levelup_update(request, pk):
    record = get_object_or_404(RobotLevelUp, pk=pk)
    institution = record.institution
    robot_materials = Material.objects.filter(vendor__vendor_type__name__icontains='로봇').order_by('name')

    if request.method == "POST":
        record.year_month = request.POST.get("year_month")  # ✅ 추가됨
        record.material_id = request.POST.get("material")
        record.section = request.POST.get("section")
        record.grade = request.POST.get("grade")
        record.class_no = request.POST.get("class_no")
        record.student_no = request.POST.get("student_no")
        record.student_name = request.POST.get("student_name")
        record.price = request.POST.get("price") or 0
        record.note = request.POST.get("note", "")
        record.save()

        messages.success(request, f"{record.student_name} 학생 정보가 수정되었습니다.")
        return redirect("robot_levelup_by_institution", institution_id=institution.id)

    return render(request, "robot_LvUP/robot_levelup_form.html", {
        "institution": institution,
        "record": record,
        "robot_materials": robot_materials,
    })



# ✅ 삭제
@login_required
def robot_levelup_delete(request, pk):
    record = get_object_or_404(RobotLevelUp, pk=pk)
    institution_id = record.institution.id if record.institution else None
    record.delete()
    messages.success(request, f"{record.student_name} 학생이 삭제되었습니다.")
    if institution_id:
        return redirect("robot_levelup_by_institution", institution_id=institution_id)
    return redirect("levelup_institution_list")



# ✅ 상태 토글
from django.utils import timezone
from django.http import JsonResponse
import pytz

@login_required
def toggle_status(request, pk, field):
    """단계업 안내/출고/전달 상태 토글"""
    record = get_object_or_404(RobotLevelUp, pk=pk)
    now = timezone.now()

    field_map = {
        "guide": ("guide_done", "guide_date"),
        "release": ("release_done", "release_date"),
        "delivery": ("delivery_done", "delivery_date"),
    }

    if field not in field_map:
        return JsonResponse({"success": False, "error": "잘못된 필드"}, status=400)

    done_field, date_field = field_map[field]
    current = getattr(record, done_field)

    # ✅ 토글 처리
    if current:
        setattr(record, done_field, False)
        setattr(record, date_field, None)
    else:
        setattr(record, done_field, True)
        setattr(record, date_field, now)

    record.save()

    # ✅ 한국시간 변환
    seoul = pytz.timezone("Asia/Seoul")
    local_date = getattr(record, date_field)
    date_str = ""
    if getattr(record, done_field) and local_date:
        local_date = local_date.astimezone(seoul)
        date_str = local_date.strftime("%y.%m.%d")

    return JsonResponse({
        "success": True,
        "done": getattr(record, done_field),
        "date": date_str
    })

# ✅ 대시보드
@login_required
def levelup_dashboard(request):
    monthly_data = (
        RobotLevelUp.objects
        .values('year_month')
        .annotate(count=Count('id'), total_price=Sum('price'))
        .order_by('year_month')
    )
    records = RobotLevelUp.objects.all()
    return render(request, 'robot_LvUP/levelup_dashboard.html', {
        'monthly_data': monthly_data,
        'records': records,
    })
