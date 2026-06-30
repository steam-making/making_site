from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, F
from django.db import transaction
from django.utils import timezone
from datetime import date
from .models import RobotLevelUp
from .forms import RobotLevelUpForm
from materials.models import Material, MaterialRelease, MaterialReleaseItem, TeachingInstitution
from students.models import Student   # ✅ 출강장소별 학생정보 추가


AUTO_RELEASE_SOURCE = "levelup_auto"
LEGACY_SHIPPED_CUTOFF = "2026-05"


def _build_levelup_release_title(institution, year_month):
    return f"{year_month} {institution.name} 단계업 자동 출고"


def _build_levelup_summary(records):
    summary = {}
    for record in records:
        if not record.material_id:
            continue
        summary[record.material_id] = summary.get(record.material_id, 0) + 1
    return summary


def find_levelup_release(institution, year_month, records=None):
    auto_release = (
        MaterialRelease.objects
        .filter(
            institution=institution,
            order_month=year_month,
            source_type=AUTO_RELEASE_SOURCE,
        )
        .prefetch_related("items")
        .first()
    )
    if auto_release:
        return auto_release

    if records is None:
        records = RobotLevelUp.objects.filter(
            institution=institution,
            year_month=year_month,
        ).select_related("material")

    target_summary = _build_levelup_summary(records)
    if not target_summary:
        return None

    candidate_releases = (
        MaterialRelease.objects
        .filter(institution=institution, order_month=year_month)
        .prefetch_related("items")
        .order_by("-created_at", "-id")
    )
    for release in candidate_releases:
        release_summary = {}
        for item in release.items.all():
            release_summary[item.material_id] = release_summary.get(item.material_id, 0) + item.quantity
        if release_summary == target_summary:
            return release

    return None


def sync_levelup_shipment_status(release):
    if not release:
        return

    records = RobotLevelUp.objects.filter(
        institution=release.institution,
        year_month=release.order_month,
    )
    if not records.exists():
        return

    records.update(shipped_done=False, shipped_date=None)

    for item in release.items.all():
        if not item.released_quantity:
            continue
        shipped_date = item.released_at.date() if item.released_at else None
        ids_to_ship = list(
            records.filter(material_id=item.material_id)
                   .order_by('created_at')
                   .values_list('id', flat=True)[:item.released_quantity]
        )
        records.filter(id__in=ids_to_ship).update(
            shipped_done=True,
            shipped_date=shipped_date,
        )


def sync_institution_shipment_status(institution):
    records = list(
        RobotLevelUp.objects.filter(institution=institution).only(
            "id", "year_month", "material_id"
        )
    )
    if not records:
        return

    month_summaries = {}
    months = set()
    for record in records:
        months.add(record.year_month)
        if not record.material_id:
            continue
        summary = month_summaries.setdefault(record.year_month, {})
        summary[record.material_id] = summary.get(record.material_id, 0) + 1

    releases = list(
        MaterialRelease.objects.filter(
            institution=institution,
            order_month__in=months,
        ).prefetch_related("items").order_by("-created_at", "-id")
    )

    matched_releases = {}
    for year_month, target_summary in month_summaries.items():
        if not target_summary:
            continue

        auto_release = next(
            (
                release for release in releases
                if release.order_month == year_month and release.source_type == AUTO_RELEASE_SOURCE
            ),
            None,
        )
        if auto_release:
            matched_releases[year_month] = auto_release
            continue

        for release in releases:
            if release.order_month != year_month:
                continue
            release_summary = {}
            for item in release.items.all():
                release_summary[item.material_id] = release_summary.get(item.material_id, 0) + item.quantity
            if release_summary == target_summary:
                matched_releases[year_month] = release
                break

    RobotLevelUp.objects.filter(institution=institution).update(shipped_done=False, shipped_date=None)
    RobotLevelUp.objects.filter(
        institution=institution,
        year_month__lt=LEGACY_SHIPPED_CUTOFF,
    ).update(
        shipped_done=True,
        shipped_date=F("release_date"),
    )

    for year_month, release in matched_releases.items():
        if year_month < LEGACY_SHIPPED_CUTOFF:
            continue
        month_records = RobotLevelUp.objects.filter(
            institution=institution,
            year_month=year_month,
        )
        for item in release.items.all():
            if not item.released_quantity:
                continue
            shipped_date = item.released_at.date() if item.released_at else None
            ids_to_ship = list(
                month_records.filter(material_id=item.material_id)
                             .order_by('created_at')
                             .values_list('id', flat=True)[:item.released_quantity]
            )
            month_records.filter(id__in=ids_to_ship).update(
                shipped_done=True,
                shipped_date=shipped_date,
            )


def _sync_levelup_release(institution, year_month, user=None):
    records = list(
        RobotLevelUp.objects.filter(
            institution=institution,
            year_month=year_month,
        ).select_related("material__vendor")
    )

    release = find_levelup_release(institution, year_month, records)

    if not records:
        if release:
            release.delete()
        return

    summary = {}
    for record in records:
        if not record.material_id:
            continue

        item = summary.setdefault(record.material_id, {
            "material": record.material,
            "vendor": record.material.vendor,
            "quantity": 0,
        })
        item["quantity"] += 1

    if not summary:
        if release:
            release.delete()
        RobotLevelUp.objects.filter(institution=institution, year_month=year_month).update(
            release_done=False,
            release_date=None,
            shipped_done=False,
            shipped_date=None,
        )
        return

    with transaction.atomic():
        if release is None:
            release = MaterialRelease.objects.create(
                teacher=institution.teacher,
                institution=institution,
                order_month=year_month,
                created_by=user,
                title=_build_levelup_release_title(institution, year_month),
                source_type=AUTO_RELEASE_SOURCE,
            )
        else:
            release.teacher = institution.teacher
            release.created_by = user or release.created_by
            release.title = release.title or _build_levelup_release_title(institution, year_month)
            release.source_type = AUTO_RELEASE_SOURCE
            release.save(update_fields=["teacher", "created_by", "title", "source_type"])

        existing_items = {item.material_id: item for item in release.items.all()}
        release.items.all().delete()

        for material_id, data in summary.items():
            material = data["material"]
            existing_item = existing_items.get(material_id)
            new_qty = data["quantity"]
            # 기존 실출고수량 보존 (단, 새 수량을 초과할 수 없음)
            old_released_qty = min(existing_item.released_quantity, new_qty) if existing_item else 0
            all_released = old_released_qty > 0 and old_released_qty >= new_qty

            MaterialReleaseItem.objects.create(
                release=release,
                vendor=data["vendor"],
                material=material,
                quantity=new_qty,
                unit_price=existing_item.unit_price if existing_item else material.school_price,
                status="released" if all_released else "pending",
                release_method=existing_item.release_method if existing_item else "택배",
                released_at=existing_item.released_at if (existing_item and all_released) else None,
                included=existing_item.included if existing_item else True,
                group_name=existing_item.group_name if existing_item else material.name,
                released_quantity=old_released_qty,
            )

        RobotLevelUp.objects.filter(institution=institution, year_month=year_month).update(
            release_done=True,
            release_date=timezone.now().date(),
        )
        sync_levelup_shipment_status(release)

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

    _sync_levelup_release(institution, year_month, request.user)

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

    # 기존 교구출고 이력을 현재 단계업 출고 상태와 맞춘다.
    sync_institution_shipment_status(institution)

    # ✅ 기본 레코드 (정렬 유지)
    records = (
        RobotLevelUp.objects
        .filter(institution=institution)
        .select_related("material", "student__division")
        .order_by(
            "-year_month",           # 년월 최신순
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
    shipped_done = records.filter(shipped_done=True).count()
    delivery_done = records.filter(delivery_done=True).count()

    # =========================================================
    # ✅ 출고 완료 · 전달 미완료 교구 (전체 요약)
    # =========================================================
    undelivered_materials = (
        records
        .filter(shipped_done=True, delivery_done=False)
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
        shipped_cnt = sum(1 for i in items if i.shipped_done)
        delivered_cnt = sum(1 for i in items if i.delivery_done)

        # 월별 전달 미완료 교구 집계
        undelivered = {}
        for i in items:
            if i.shipped_done and not i.delivery_done:
                name = i.material.name
                undelivered[name] = undelivered.get(name, 0) + 1

        # ✅ 월별 출고 교구 집계
        release_materials = {}
        for i in items:
            if i.release_done:
                name = i.material.name
                release_materials[name] = release_materials.get(name, 0) + 1

        # ⭐ 교구명 오름차순 정렬
        release_materials = dict(sorted(release_materials.items()))

        monthly_stats[ym] = {
            "total": total_cnt,
            "guide_done": guide_cnt,
            "release_done": release_cnt,
            "shipped_done": shipped_cnt,
            "delivered": delivered_cnt,
            "undelivered": undelivered,
            "release_materials": release_materials,
            "all_done": (
                guide_cnt == total_cnt
                and release_cnt == total_cnt
                and shipped_cnt == total_cnt
                and delivered_cnt == total_cnt
            ),
        }


    # =========================================================
    # ✅ 렌더링
    # =========================================================
    return render(request, "robot_LvUP/robot_levelup_list.html", {
        # 기본
        "institution": institution,
        "institutions": TeachingInstitution.objects.all() if request.user.is_staff else TeachingInstitution.objects.filter(teacher=request.user),
        "records": records,

        # 전체 통계
        "total": total,
        "total_price": total_price,
        "guide_done": guide_done,
        "release_done": release_done,
        "shipped_done": shipped_done,
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

            student_id = request.POST.get(f"student_id_{i}") or None

            # ✅ 필수값 확인
            if not (student_name and material_id):
                continue

            # ✅ DB 저장
            RobotLevelUp.objects.create(
                institution=institution,
                year_month=year_month,
                material_id=material_id,
                student_id=student_id,
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
            _sync_levelup_release(institution, year_month, request.user)
            messages.success(request, f"단계업 등록이 완료되었고 교구출고에도 자동 반영되었습니다. (총 {created}건)")
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
    before_institution = record.institution
    before_year_month = record.year_month

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

        if before_institution and before_year_month:
            _sync_levelup_release(before_institution, before_year_month, request.user)
        if record.institution and (record.institution_id != getattr(before_institution, "id", None) or record.year_month != before_year_month):
            _sync_levelup_release(record.institution, record.year_month, request.user)

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
    sync_institution = record.institution
    sync_year_month = record.year_month
    record.delete()
    if sync_institution and sync_year_month:
        _sync_levelup_release(sync_institution, sync_year_month, request.user)
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


@login_required
def toggle_shipped_student(request, pk):
    """모달에서 개별 학생 출고 토글 → MaterialReleaseItem released_quantity 자동 동기화"""
    from materials.models import MaterialReleaseItem
    record = get_object_or_404(RobotLevelUp, pk=pk)

    record.shipped_done = not record.shipped_done
    record.shipped_date = timezone.now().date() if record.shipped_done else None
    record.save(update_fields=["shipped_done", "shipped_date"])

    # 매칭된 출고 아이템의 released_quantity 재계산
    release = find_levelup_release(record.institution, record.year_month)
    if release:
        item = release.items.filter(material=record.material).first()
        if item:
            shipped_count = RobotLevelUp.objects.filter(
                institution=record.institution,
                year_month=record.year_month,
                material=record.material,
                shipped_done=True,
            ).count()
            item.released_quantity = shipped_count
            if shipped_count >= item.quantity:
                item.status = "released"
                if not item.released_at:
                    item.released_at = timezone.now()
            else:
                item.status = "pending"
                item.released_at = None
            item.save(update_fields=["released_quantity", "status", "released_at"])

    return JsonResponse({
        "success": True,
        "shipped": record.shipped_done,
        "date": record.shipped_date.strftime("%y-%m-%d") if record.shipped_date else "",
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
