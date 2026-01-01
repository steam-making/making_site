# teachers/views.py
from django import forms
from .forms import TeachingInstitutionForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.contrib.auth.models import User
from .models import TeachingInstitution, TeachingDay
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Certificate, Career
from .forms import CertificateForm, CareerForm




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
    selected_teacher_id = request.GET.get('teacher')

    # 🔷 전체 강사 (필터 드롭다운용)
    teachers = User.objects.filter(profile__user_type='teacher').order_by('first_name')

    # 🔷 강사 또는 관리자에 따라 조회 범위 다르게 설정
    if request.user.is_superuser:
        if selected_teacher_id:
            institutions = TeachingInstitution.objects.filter(teacher_id=selected_teacher_id)
        else:
            institutions = TeachingInstitution.objects.all()
    else:
        institutions = TeachingInstitution.objects.filter(teacher=request.user)

    context = {
        'teachers': teachers,
        'institutions': institutions,
        'selected_teacher_id': int(selected_teacher_id) if selected_teacher_id else None,
    }
    return render(request, 'teachers/institution_list.html', context)


@login_required
def add_institution(request):
    if request.method == 'POST':
        form = TeachingInstitutionForm(request.POST)
        if form.is_valid():
            institution = form.save(commit=False)

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
            form.fields['teacher'].widget = forms.HiddenInput()
    return render(request, 'teachers/add_institution.html', {'form': form})


@login_required
def teacher_dashboard(request):
    return render(request, 'teachers/teacher_dashboard.html')


@login_required
def institution_update(request, pk):
    inst = get_object_or_404(TeachingInstitution, pk=pk)

    # 🔐 권한 체크
    if not request.user.is_staff and inst.teacher != request.user:
        messages.error(request, "수정 권한이 없습니다.")
        return redirect('institution_list')

    if request.method == "POST":
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