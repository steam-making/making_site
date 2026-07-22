# teachers/views.py
from django import forms
from .forms import TeachingInstitutionForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.db.models import Q, Count, Max
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import datetime, date
from django.contrib.auth.models import User
from .models import TeachingInstitution, TeachingDay
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Certificate, Career, CertificateCatalogItem
from django.http import HttpResponseForbidden
from .forms import CertificateForm, CareerForm
from collections import OrderedDict




def teacher_career_list(request, teacher_id):
    teacher = get_object_or_404(User, id=teacher_id)
    careers = Career.objects.filter(teacher=teacher).order_by('-start_date', '-end_date')
    return render(request, 'teachers/career_list_by_teacher.html', {
        'teacher': teacher,
        'careers': careers,
    })

def teacher_certificate_list(request, teacher_id):
    teacher = get_object_or_404(User, id=teacher_id)
    certificates = Certificate.objects.filter(teacher=teacher).order_by("issued_date")
    return render(request, 'teachers/certificate_list_by_teacher.html', {
        'teacher': teacher,
        'certificates': certificates,
    })

def is_admin(user):
    return user.is_superuser

# teachers/views.py
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import TeachingInstitution
from django.shortcuts import render

@login_required
def institution_list(request):
    teacher_query = request.GET.get('teacher_q', '').strip()
    selected_teacher_id = request.GET.get('teacher_id', '').strip()
    institution_query = request.GET.get('institution_q', '').strip()
    program_query = request.GET.get('program_q', '').strip()

    teachers = User.objects.filter(profile__user_type='teacher').order_by('first_name')

    if request.user.is_staff:
        institutions = TeachingInstitution.objects.select_related('teacher', 'school').prefetch_related('days').all()
        if selected_teacher_id.isdigit():
            institutions = institutions.filter(teacher_id=int(selected_teacher_id))
        if teacher_query:
            institutions = institutions.filter(
                Q(teacher__first_name__icontains=teacher_query)
                | Q(teacher__username__icontains=teacher_query)
            )
    else:
        institutions = TeachingInstitution.objects.select_related('teacher', 'school').prefetch_related('days').filter(teacher=request.user)

    if institution_query:
        institutions = institutions.filter(
            Q(school__name__icontains=institution_query)
            | Q(name__icontains=institution_query)
        )

    if program_query:
        institutions = institutions.filter(program__icontains=program_query)

    institutions = institutions.order_by('teacher__first_name', 'teacher__username', 'is_closed', '-created_at')

    grouped_institutions = OrderedDict()
    for institution in institutions:
        teacher_name = institution.teacher.first_name or institution.teacher.username
        grouped_institutions.setdefault(teacher_name, []).append(institution)

    context = {
        'teachers': teachers,
        'grouped_institutions': grouped_institutions,
        'teacher_query': teacher_query,
        'selected_teacher_id': selected_teacher_id,
        'institution_query': institution_query,
        'program_query': program_query,
        'today': timezone.now().date(),
    }
    return render(request, 'teachers/institution_list.html', context)


@login_required
def add_institution(request):
    template_name = 'teachers/institution_form.html'

    if request.method == 'POST':
        form = TeachingInstitutionForm(request.POST)
        if form.is_valid():
            institution = form.save(commit=False)

            if request.user.is_staff:
                teacher_id = form.cleaned_data.get("teacher_choice")
                if teacher_id:
                    institution.teacher_id = int(teacher_id)
                else:
                    form.add_error("teacher_choice", "강사를 선택해주세요.")
                    return render(request, template_name, {
                        'form': form,
                        'title': '출강 등록',
                        'submit_label': '등록하기',
                        'school_id': '',
                        'school_name': '',
                    })
            else:
                institution.teacher = request.user

            place_type = form.cleaned_data.get("place_type")

            # 🔹 학교 / 유치원 → school FK 사용
            if place_type in ["school"]:
                institution.school = form.cleaned_data.get("school")
                institution.name = institution.school.name if institution.school else ""

            # 🔹 기타 기관 계열 → name 직접 입력
            else:
                institution.school = None
                institution.name = form.cleaned_data.get("name")

            institution.save()
            form.save_m2m()
            return redirect('institution_list')
    else:
        form = TeachingInstitutionForm()
        if not request.user.is_staff:
            form.fields['teacher_choice'].widget = forms.HiddenInput()
            form.fields['teacher_choice'].required = False
            form.initial['teacher_choice'] = str(request.user.id)
    return render(request, template_name, {
        'form': form,
        'title': '출강 등록',
        'submit_label': '등록하기',
        'school_id': '',
        'school_name': '',
    })


@login_required
def teacher_dashboard(request):
    profile = getattr(request.user, "profile", None)
    user_type = getattr(profile, "user_type", "")

    if not request.user.is_staff and user_type not in ("teacher", "center_teacher"):
        return redirect("home")

    from students.models import ProgramDivision, Student
    from tasks.models import Task
    from notices.models import Notice
    from materials.models import MaterialRelease

    institutions = (
        TeachingInstitution.objects
        .filter(teacher=request.user)
        .annotate(student_count=Count("divisions__students", distinct=True))
        .prefetch_related("days", "divisions")
        .order_by("is_closed", "school__name", "name", "program")
    )

    active_institutions = institutions.filter(is_closed=False)
    total_students = Student.objects.filter(division__institution__teacher=request.user).count()
    total_divisions = ProgramDivision.objects.filter(institution__teacher=request.user).count()
    total_certificates = Certificate.objects.filter(teacher=request.user).count()
    total_careers = Career.objects.filter(teacher=request.user).count()

    open_tasks = Task.objects.filter(created_by=request.user, completed=False)
    due_soon_tasks = open_tasks.filter(due_date__isnull=False, due_date__lte=timezone.now().date())

    release_queryset = MaterialRelease.objects.filter(teacher=request.user)
    recent_releases = (
        release_queryset
        .select_related("institution")
        .order_by("-created_at")[:5]
    )
    unpaid_releases = release_queryset.filter(
        payment_status__in=["unpaid", "partial"],
    ).count()

    notices = (
        Notice.objects
        .filter(status="published", audience__in=["all", "teacher"])
        .order_by("-is_pinned", "-published_at")[:5]
    )

    context = {
        "dashboard_role": "센터 강사" if user_type == "center_teacher" else "강사",
        "institutions": institutions[:6],
        "institution_count": institutions.count(),
        "active_institution_count": active_institutions.count(),
        "closed_institution_count": institutions.filter(is_closed=True).count(),
        "total_students": total_students,
        "total_divisions": total_divisions,
        "total_certificates": total_certificates,
        "total_careers": total_careers,
        "open_tasks_count": open_tasks.count(),
        "due_soon_tasks_count": due_soon_tasks.count(),
        "total_releases_count": release_queryset.count(),
        "upcoming_tasks": open_tasks.order_by("due_date", "-created_at")[:5],
        "recent_releases": recent_releases,
        "unpaid_releases_count": unpaid_releases,
        "notices": notices,
        "today": timezone.now().date(),
    }
    return render(request, 'teachers/teacher_dashboard.html', context)


@login_required
def institution_update(request, pk):
    inst = get_object_or_404(TeachingInstitution, pk=pk)

    # 🔐 권한 체크
    if not request.user.is_staff and inst.teacher != request.user:
        messages.error(request, "수정 권한이 없습니다.")
        return redirect('institution_list')

    if inst.is_closed:
        messages.warning(request, "종료된 출강 장소는 수정할 수 없습니다.")
        return redirect('institution_list')

    if request.method == "POST":
        inst.refresh_from_db(fields=["is_closed"])
        if inst.is_closed:
            messages.warning(request, "종료된 출강 장소는 수정할 수 없습니다.")
            return redirect('institution_list')

        form = TeachingInstitutionForm(request.POST, instance=inst)

        if not form.is_valid():
            print("❌ FORM ERRORS:", form.errors)
        else:
            institution = form.save(commit=False)

            # ⭐ ChoiceField → FK 직접 매핑
            teacher_id = form.cleaned_data.get("teacher_choice")
            if teacher_id:
                institution.teacher_id = int(teacher_id)

            institution.save()
            form.save_m2m()

            messages.success(request, "출강장소가 수정되었습니다.")
            return redirect('institution_list')

    else:
        # 🔥 initial은 teacher_choice만 설정
        initial = {}
        if inst.teacher_id:
            initial["teacher_choice"] = str(inst.teacher_id)

        form = TeachingInstitutionForm(
            instance=inst,
            initial=initial
        )

        if not request.user.is_staff:
            form.fields["teacher_choice"].disabled = True

    return render(request, 'teachers/institution_form.html', {
        'form': form,
        'title': '출강 수정',
        'submit_label': '수정하기',
        'school_id': inst.school.id if inst.school else "",
        'school_name': inst.school.name if inst.school else "",
    })


@login_required
@require_POST
def institution_delete(request, pk):
    inst = get_object_or_404(TeachingInstitution, pk=pk)

    if not request.user.is_staff and inst.teacher != request.user:
        messages.error(request, "삭제 권한이 없습니다.")
        return redirect('institution_list')

    if inst.is_closed:
        messages.warning(request, "종료된 출강 장소는 삭제할 수 없습니다.")
        return redirect('institution_list')

    inst.delete()
    messages.success(request, "출강 장소가 삭제되었습니다.")
    return redirect('institution_list')


@login_required
@require_POST
def institution_close(request, pk):
    inst = get_object_or_404(TeachingInstitution, pk=pk)

    if not request.user.is_staff and inst.teacher != request.user:
        messages.error(request, "종료 권한이 없습니다.")
        return redirect('institution_list')

    close_date_raw = (request.POST.get("close_date") or "").strip()
    closed_at = timezone.now()
    if close_date_raw:
        try:
            close_date = datetime.strptime(close_date_raw, "%Y-%m-%d").date()
            closed_at = timezone.make_aware(datetime.combine(close_date, datetime.min.time()))
        except ValueError:
            messages.error(request, "종료일 형식이 올바르지 않습니다.")
            return redirect('institution_list')

    updated = TeachingInstitution.objects.filter(pk=inst.pk, is_closed=False).update(
        is_closed=True,
        closed_at=closed_at,
    )

    if updated == 0:
        messages.info(request, "이미 종료된 출강 장소입니다.")
        return redirect('institution_list')

    messages.success(request, "출강 장소가 종료 처리되었습니다.")
    return redirect('institution_list')




    
    
def _parse_material_cost(materials_text):
    import re
    if not materials_text:
        return None
    match = re.search(r'([\d,]+)\s*원', materials_text)
    if match:
        return int(match.group(1).replace(",", ""))
    return None


def _safe_parse_cost(val, fallback):
    from recruit.views import parse_cost
    try:
        return parse_cost(val)
    except (TypeError, ValueError):
        return fallback


def _sync_related_recruit(item):
    """자격증리스트 항목을 저장할 때, 연결된 지도사과정 모집공고(및 과정 템플릿)에도 반영한다."""
    if not item.related_recruit_id:
        return

    recruit = item.related_recruit
    recruit.certificate_agency = item.issuer
    recruit.cost_education = _safe_parse_cost(item.education_fee, recruit.cost_education)
    recruit.cost_certificate = _safe_parse_cost(item.issue_fee, recruit.cost_certificate)
    material_cost = _parse_material_cost(item.materials)
    if material_cost is not None:
        recruit.cost_material = material_cost
    curriculum = item.curriculum_list()
    if curriculum:
        recruit.curriculum = [
            {"session": str(i + 1), "content": line, "time": "1"}
            for i, line in enumerate(curriculum)
        ]
    recruit.save(update_fields=[
        "certificate_agency", "cost_education", "cost_certificate", "cost_material", "curriculum",
    ])

    course_type = recruit.course_type
    if course_type:
        course_type.certificate_agency = item.issuer
        course_type.cost_education = recruit.cost_education
        course_type.cost_certificate = recruit.cost_certificate
        course_type.cost_material = recruit.cost_material
        if curriculum:
            course_type.curriculum = recruit.curriculum
        course_type.save(update_fields=[
            "certificate_agency", "cost_education", "cost_certificate", "cost_material", "curriculum",
        ])


def _catalog_item_to_dict(item):
    return {
        "id": item.id,
        "category": item.category,
        "auth_type": item.auth_type,
        "name": item.name,
        "issuer": item.issuer,
        "related_recruit_id": item.related_recruit_id,
        "detail": {
            "validity": item.validity,
            "issue_fee": item.issue_fee,
            "education_fee": item.education_fee,
            "materials": item.materials,
            "min_students": item.min_students,
            "session_length": item.session_length,
            "session_count": item.session_count,
            "curriculum": item.curriculum_list(),
            "exam_type": item.exam_type,
            "exam_fee": item.exam_fee,
            "related_link": item.related_link,
        },
    }


@login_required
def certificate_catalog(request):
    """취득 대상 자격증 리스트(카탈로그) - 지도사자격/기타자격 안내 + 취득 여부 관리"""
    from recruit.models import InstructorRecruit

    my_certs = {c.name: c for c in Certificate.objects.filter(teacher=request.user)}
    items = CertificateCatalogItem.objects.select_related('related_recruit').all()

    catalog = []
    catalog_for_js = []
    for item in items:
        acquired = my_certs.get(item.name)
        row = _catalog_item_to_dict(item)
        row["acquired_date"] = acquired.issued_date if acquired else None
        row["recruit_open"] = bool(item.related_recruit and item.related_recruit.status == "open")
        catalog.append(row)
        catalog_for_js.append(_catalog_item_to_dict(item))

    return render(request, 'teachers/certificate_catalog.html', {
        'catalog': catalog,
        'catalog_for_js': catalog_for_js,
        'recruit_choices': InstructorRecruit.objects.select_related('course_type').order_by('-created_at'),
    })


@login_required
def certificate_catalog_acquire(request):
    """카탈로그에서 '취득' 처리 -> 내 자격증관리(Certificate)에 추가"""
    if request.method != "POST":
        return redirect('certificate_catalog')

    cert_id = request.POST.get("cert_id")
    year = request.POST.get("year")
    month = request.POST.get("month")

    item = CertificateCatalogItem.objects.filter(id=cert_id).first()
    if not item:
        messages.error(request, "존재하지 않는 자격증입니다.")
        return redirect('certificate_catalog')

    try:
        issued_date = date(int(year), int(month), 1)
    except (TypeError, ValueError):
        messages.error(request, "취득년월을 올바르게 선택해주세요.")
        return redirect('certificate_catalog')

    Certificate.objects.update_or_create(
        teacher=request.user,
        name=item.name,
        defaults={"issued_by": item.issuer, "issued_date": issued_date},
    )
    messages.success(request, f"'{item.name}'이(가) 자격증관리에 추가되었습니다.")
    return redirect('certificate_catalog')


@login_required
def certificate_catalog_save(request):
    """관리자 전용: 카탈로그 항목 추가/수정"""
    if not request.user.is_staff:
        return HttpResponseForbidden("접근 권한이 없습니다.")
    if request.method != "POST":
        return redirect('certificate_catalog')

    item_id = request.POST.get("item_id")
    if item_id:
        item = get_object_or_404(CertificateCatalogItem, id=item_id)
    else:
        item = CertificateCatalogItem()
        max_order = CertificateCatalogItem.objects.aggregate(Max('order'))['order__max'] or 0
        item.order = max_order + 1

    item.category = request.POST.get("category", "").strip()
    item.auth_type = request.POST.get("auth_type", "").strip()
    item.name = request.POST.get("name", "").strip()
    item.issuer = request.POST.get("issuer", "").strip()
    item.validity = request.POST.get("validity", "").strip()
    item.issue_fee = request.POST.get("issue_fee", "").strip()
    item.education_fee = request.POST.get("education_fee", "").strip()
    item.materials = request.POST.get("materials", "").strip()
    item.min_students = request.POST.get("min_students", "").strip()
    item.session_length = request.POST.get("session_length", "").strip()
    session_count = request.POST.get("session_count", "").strip()
    item.session_count = int(session_count) if session_count.isdigit() else None
    item.curriculum = request.POST.get("curriculum", "").strip()
    item.exam_type = request.POST.get("exam_type", "").strip()
    item.exam_fee = request.POST.get("exam_fee", "").strip()
    item.related_link = request.POST.get("related_link", "").strip()

    related_recruit_id = request.POST.get("related_recruit_id", "").strip()
    item.related_recruit_id = int(related_recruit_id) if related_recruit_id.isdigit() else None

    if not item.name:
        messages.error(request, "자격증명을 입력해주세요.")
        return redirect('certificate_catalog')

    item.save()
    _sync_related_recruit(item)
    messages.success(request, f"'{item.name}'이(가) 저장되었습니다.")
    return redirect('certificate_catalog')


@require_POST
@login_required
def certificate_catalog_delete(request, item_id):
    """관리자 전용: 카탈로그 항목 삭제"""
    if not request.user.is_staff:
        return HttpResponseForbidden("접근 권한이 없습니다.")

    item = get_object_or_404(CertificateCatalogItem, id=item_id)
    name = item.name
    item.delete()
    messages.success(request, f"'{name}'이(가) 삭제되었습니다.")
    return redirect('certificate_catalog')


@login_required
def certificate_list(request):
    certificates = Certificate.objects.filter(teacher=request.user)
    return render(request, 'teachers/certificate_list.html', {'certificates': certificates})

@login_required
def certificate_create(request):
    if request.method == 'POST':
        form = CertificateForm(request.POST)
        if form.is_valid():
            cert = form.save(commit=False)
            cert.teacher = request.user
            cert.save()
            return redirect('certificate_list')
    else:
        form = CertificateForm()
    return render(request, 'teachers/certificate_form.html', {'form': form})

@login_required
def certificate_update(request, pk):
    # ✅ 본인(User) 소유 자격증만 수정 가능
    cert = get_object_or_404(Certificate, pk=pk, teacher=request.user)
    if request.method == "POST":
        form = CertificateForm(request.POST, instance=cert)
        if form.is_valid():
            form.save()
            messages.success(request, "자격증이 수정되었습니다.")
            return redirect("certificate_list")
    else:
        form = CertificateForm(instance=cert)
    return render(request, "teachers/certificate_form.html", {"form": form})

@login_required
def certificate_delete(request, pk):
    cert = get_object_or_404(Certificate, pk=pk, teacher=request.user)
    if request.method == "POST":
        cert.delete()
        messages.success(request, "자격증이 삭제되었습니다.")
    return redirect("certificate_list")


@login_required
def career_list(request):
    careers = Career.objects.filter(teacher=request.user)
    return render(request, 'teachers/career_list.html', {'careers': careers})

@login_required
def career_create(request):
    if request.method == 'POST':
        form = CareerForm(request.POST)
        if form.is_valid():
            career = form.save(commit=False)
            career.teacher = request.user
            career.save()
            return redirect('career_list')
    else:
        form = CareerForm()
    return render(request, 'teachers/career_form.html', {'form': form})

@login_required
def career_update(request, pk):
    # ✅ Career.teacher = User FK 이므로 request.user 로 필터링
    career = get_object_or_404(Career, pk=pk, teacher=request.user)
    if request.method == "POST":
        form = CareerForm(request.POST, instance=career)
        if form.is_valid():
            form.save()
            messages.success(request, "경력이 수정되었습니다.")
            return redirect("career_list")
    else:
        form = CareerForm(instance=career)
    return render(request, "teachers/career_form.html", {"form": form})


@login_required
def career_delete(request, pk):
    career = get_object_or_404(Career, pk=pk, teacher=request.user)
    if request.method == "POST":
        career.delete()
        messages.success(request, "경력이 삭제되었습니다.")
    return redirect("career_list")
