import json
import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from students.models import ProgramDivision, Student
from teachers.models import TeachingInstitution

from .forms import GroupSeatForm
from .models import Seat, SeatAssignment, SeatGroup, SeatLayout


def _seat_manage_url(institution_id, division_id=None):
    url = reverse('seating:seat_manage', args=[institution_id])
    if division_id:
        url += f"?division={division_id}"
    return url


def _return_url(request, institution_id, division_id):
    """자동배정 등 액션 후 어디로 돌아갈지: 전체화면에서 실행했으면 전체화면으로, 아니면 관리 화면으로"""
    if request.POST.get('return_to') == 'fullscreen' and division_id:
        return reverse('seating:seat_fullscreen', args=[institution_id, division_id])
    return _seat_manage_url(institution_id, division_id)


def _check_access(request, institution):
    if not request.user.is_staff and institution.teacher != request.user:
        return False
    return True


def _selectable_divisions(institution):
    return (
        ProgramDivision.objects
        .filter(institution=institution)
        .exclude(division__icontains="미수강")
        .order_by('division')
    )


def _division_students(division):
    return Student.objects.filter(division=division).order_by('grade', 'class_name', 'number')


def _build_layout_rows(layout, division):
    """레이아웃의 조들을 행별로 묶고, 지정된 부서의 현재 좌석 배정을 채워서 반환"""
    if not layout:
        return []

    assignment_qs = SeatAssignment.objects.none()
    if division:
        assignment_qs = SeatAssignment.objects.filter(division=division).select_related('student')

    groups = list(
        layout.groups.prefetch_related(
            Prefetch('seats__assignments', queryset=assignment_qs, to_attr='division_assignments')
        ).order_by('position_row', 'position_col')
    )
    for group in groups:
        for seat in group.seats.all():
            seat.current_assignment = seat.division_assignments[0] if seat.division_assignments else None

    rows_map = {}
    for group in groups:
        rows_map.setdefault(group.position_row, []).append(group)
    return [rows_map[r] for r in sorted(rows_map.keys())]


@login_required
def seat_manage(request, institution_id):
    institution = get_object_or_404(TeachingInstitution, id=institution_id)
    if not _check_access(request, institution):
        return HttpResponseForbidden("접근 권한이 없습니다.")

    divisions = list(_selectable_divisions(institution))

    division = None
    division_id = request.GET.get('division')
    if division_id:
        division = next((d for d in divisions if str(d.id) == str(division_id)), None)
    if division is None and divisions:
        division = divisions[0]

    layout = SeatLayout.objects.filter(institution=institution).first()
    layout_rows = _build_layout_rows(layout, division)
    students = Student.objects.none()
    assigned_count = 0

    if layout and division:
        assigned_count = SeatAssignment.objects.filter(
            seat__group__layout=layout, division=division
        ).count()

    if division:
        students = _division_students(division)

    current_row_cols = layout.get_row_col_counts() if layout else [2, 2]

    return render(request, 'seating/seat_manage.html', {
        'institution': institution,
        'divisions': divisions,
        'division': division,
        'layout': layout,
        'layout_rows': layout_rows,
        'current_row_cols': current_row_cols,
        'students': students,
        'assigned_count': assigned_count,
        'unseated_count': students.count() - assigned_count,
    })


@login_required
def seat_fullscreen(request, institution_id, division_id):
    institution = get_object_or_404(TeachingInstitution, id=institution_id)
    if not _check_access(request, institution):
        return HttpResponseForbidden("접근 권한이 없습니다.")
    division = get_object_or_404(ProgramDivision, id=division_id, institution=institution)

    layout = SeatLayout.objects.filter(institution=institution).first()
    if not layout:
        messages.error(request, "먼저 조 배치를 생성해주세요.")
        return redirect(_seat_manage_url(institution.id, division.id))

    layout_rows = _build_layout_rows(layout, division)

    return render(request, 'seating/seat_fullscreen.html', {
        'institution': institution,
        'division': division,
        'layout_rows': layout_rows,
    })


@login_required
@require_POST
def set_group_grid(request, institution_id):
    institution = get_object_or_404(TeachingInstitution, id=institution_id)
    if not _check_access(request, institution):
        return HttpResponseForbidden("접근 권한이 없습니다.")
    division_id = request.POST.get('division')

    raw_row_cols = request.POST.getlist('row_cols')
    row_col_counts = []
    for raw in raw_row_cols:
        raw = (raw or '').strip()
        if not raw.isdigit() or not (1 <= int(raw) <= 10):
            messages.error(request, "행별 조 열 수는 1~10 사이의 숫자로 입력해주세요.")
            return redirect(_seat_manage_url(institution.id, division_id))
        row_col_counts.append(int(raw))

    if not row_col_counts or len(row_col_counts) > 10:
        messages.error(request, "행 수는 1~10 사이로 입력해주세요.")
        return redirect(_seat_manage_url(institution.id, division_id))

    with transaction.atomic():
        layout, _ = SeatLayout.objects.get_or_create(institution=institution)
        layout.row_col_counts = ",".join(str(n) for n in row_col_counts)
        layout.save(update_fields=['row_col_counts'])

        existing = {(g.position_row, g.position_col): g for g in layout.groups.all()}
        wanted_positions = [
            (row_no, col_no)
            for row_no, cols in enumerate(row_col_counts, start=1)
            for col_no in range(1, cols + 1)
        ]

        # 범위 밖으로 밀려난 조는 삭제 (좌석/배정도 함께 삭제됨)
        for pos, group in existing.items():
            if pos not in wanted_positions:
                group.delete()

        # 새로 필요한 위치에는 기본 2x2 좌석의 조를 새로 생성 (기존 조는 그대로 유지)
        next_no = layout.groups.count() + 1
        for pos in wanted_positions:
            if pos not in existing:
                group = SeatGroup.objects.create(
                    layout=layout, name=f"{next_no}조",
                    position_row=pos[0], position_col=pos[1],
                    seat_rows=2, seat_cols=2,
                )
                for seat_no in range(1, 2 * 2 + 1):
                    Seat.objects.create(group=group, seat_number=seat_no)
                next_no += 1

    messages.success(request, "조 배치를 적용했습니다. (1부/2부/3부 공통으로 적용됩니다) 각 조의 좌석 행/열을 필요에 따라 조정해주세요.")
    return redirect(_seat_manage_url(institution.id, division_id))


@login_required
@require_POST
def set_all_group_seats(request, institution_id):
    """모든 조의 좌석 행/열을 한 번에 적용 (조별 개별 적용 버튼 대신 전체 적용 버튼 하나로 처리)"""
    institution = get_object_or_404(TeachingInstitution, id=institution_id)
    if not _check_access(request, institution):
        return HttpResponseForbidden("접근 권한이 없습니다.")
    layout = get_object_or_404(SeatLayout, institution=institution)
    division_id = request.POST.get('division')

    groups = list(layout.groups.all())
    to_update = []
    for group in groups:
        form = GroupSeatForm({
            'seat_rows': request.POST.get(f'seat_rows_{group.id}'),
            'seat_cols': request.POST.get(f'seat_cols_{group.id}'),
        })
        if not form.is_valid():
            messages.error(request, f"{group.name}의 좌석 행/열 값을 확인해주세요.")
            return redirect(_seat_manage_url(institution.id, division_id))

        seat_rows = form.cleaned_data['seat_rows']
        seat_cols = form.cleaned_data['seat_cols']
        if seat_rows != group.seat_rows or seat_cols != group.seat_cols:
            to_update.append((group, seat_rows, seat_cols))

    if not to_update:
        messages.info(request, "변경된 조의 좌석 배치가 없습니다.")
        return redirect(_seat_manage_url(institution.id, division_id))

    with transaction.atomic():
        for group, seat_rows, seat_cols in to_update:
            group.seat_rows = seat_rows
            group.seat_cols = seat_cols
            group.save(update_fields=['seat_rows', 'seat_cols'])
            group.seats.all().delete()
            for seat_no in range(1, seat_rows * seat_cols + 1):
                Seat.objects.create(group=group, seat_number=seat_no)

    changed_names = ", ".join(g.name for g, _, _ in to_update)
    messages.success(
        request,
        f"{len(to_update)}개 조({changed_names})의 좌석 배치를 변경했습니다. (해당 조들의 모든 부서 배정은 초기화됩니다)"
    )
    return redirect(_seat_manage_url(institution.id, division_id))


@login_required
@require_POST
def set_priority_students(request, institution_id, division_id):
    institution = get_object_or_404(TeachingInstitution, id=institution_id)
    if not _check_access(request, institution):
        return HttpResponseForbidden("접근 권한이 없습니다.")
    division = get_object_or_404(ProgramDivision, id=division_id, institution=institution)

    selected_ids = request.POST.getlist('priority_students')
    students = _division_students(division)
    students.update(is_priority=False)
    students.filter(id__in=selected_ids).update(is_priority=True)

    messages.success(request, "우선배정 학생 설정을 저장했습니다.")
    return redirect(_seat_manage_url(institution.id, division.id))


@login_required
@require_POST
def assign_random_seats(request, institution_id, division_id):
    institution = get_object_or_404(TeachingInstitution, id=institution_id)
    if not _check_access(request, institution):
        return HttpResponseForbidden("접근 권한이 없습니다.")
    division = get_object_or_404(ProgramDivision, id=division_id, institution=institution)

    layout = SeatLayout.objects.filter(institution=institution).first()
    if not layout:
        messages.error(request, "먼저 조 배치를 생성해주세요.")
        return redirect(_return_url(request, institution.id, division.id))

    students = _division_students(division)
    priority_students = list(students.filter(is_priority=True))
    other_students = list(students.filter(is_priority=False))
    random.shuffle(other_students)

    all_seats = list(
        Seat.objects.filter(group__layout=layout)
        .select_related('group')
        .order_by('group__position_row', 'group__position_col', 'seat_number')
    )

    ordered_students = priority_students + other_students
    with transaction.atomic():
        # 이 부서의 기존 배정만 지우고, 다른 부서(1부/2부/3부)가 쓰던 배정은 그대로 둔다
        SeatAssignment.objects.filter(seat__group__layout=layout, division=division).delete()
        SeatAssignment.objects.bulk_create([
            SeatAssignment(seat=seat, division=division, student=student)
            for seat, student in zip(all_seats, ordered_students)
        ])

    if len(ordered_students) > len(all_seats):
        messages.warning(
            request,
            f"학생 수({len(ordered_students)}명)가 좌석 수({len(all_seats)}개)보다 많아 "
            f"{len(ordered_students) - len(all_seats)}명은 배정되지 못했습니다."
        )
    else:
        messages.success(request, "자리를 자동으로 배정했습니다.")
    return redirect(_return_url(request, institution.id, division.id))


@login_required
@require_POST
def swap_seats(request):
    try:
        data = json.loads(request.body)
        seat1_id = data.get('seat1')
        seat2_id = data.get('seat2')
        division_id = data.get('division')
        seat1 = Seat.objects.select_related('group__layout__institution').get(id=seat1_id)
        seat2 = Seat.objects.select_related('group__layout__institution').get(id=seat2_id)
        division = ProgramDivision.objects.get(id=division_id)
    except (ValueError, TypeError, Seat.DoesNotExist, ProgramDivision.DoesNotExist):
        return JsonResponse({'status': 'error', 'message': '좌석 또는 부서를 찾을 수 없습니다.'}, status=400)

    inst1 = seat1.group.layout.institution
    inst2 = seat2.group.layout.institution
    if inst1.id != inst2.id or inst1.id != division.institution_id:
        return JsonResponse({'status': 'error', 'message': '같은 학교의 좌석끼리만 교환할 수 있습니다.'}, status=400)
    if not _check_access(request, inst1):
        return JsonResponse({'status': 'error', 'message': '권한이 없습니다.'}, status=403)

    a1 = SeatAssignment.objects.filter(seat=seat1, division=division).first()
    a2 = SeatAssignment.objects.filter(seat=seat2, division=division).first()

    with transaction.atomic():
        s1_student = a1.student if a1 else None
        s2_student = a2.student if a2 else None
        if a1:
            a1.delete()
        if a2:
            a2.delete()
        if s2_student:
            SeatAssignment.objects.create(seat=seat1, division=division, student=s2_student)
        if s1_student:
            SeatAssignment.objects.create(seat=seat2, division=division, student=s1_student)

    return JsonResponse({'status': 'success'})
