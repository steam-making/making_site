from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import SignUpForm
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from .forms import UserUpdateForm, CustomPasswordChangeForm
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import render
import requests
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from .models import KakaoToken
from django.utils import timezone
from datetime import timedelta
from .models import Profile, Child
from .forms import ChildForm
from .forms import InstitutionSignUpForm


def kakao_login(request):
    client_id = settings.KAKAO_REST_API_KEY  # settings.py에 등록 필요
    redirect_uri = "http://127.0.0.1:8000/oauth/kakao/callback/" if settings.DEBUG else "http://133.186.144.151/oauth/kakao/callback/"
    kakao_auth_url = (
        f"https://kauth.kakao.com/oauth/authorize?"
        f"client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=talk_message"
    )
    return redirect(kakao_auth_url)

def kakao_callback(request):
    code = request.GET.get("code")
    if not code:
        return HttpResponse("인가 코드가 없습니다.", status=400)

    token_url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": settings.KAKAO_REST_API_KEY,
        "redirect_uri": (
            "http://127.0.0.1:8000/oauth/kakao/callback/"
            if settings.DEBUG else
            "http://133.186.144.151/oauth/kakao/callback/"
        ),
        "code": code,
    }
    res = requests.post(token_url, data=data)
    token_json = res.json()
    print("🔍 카카오 토큰 요청 데이터:", data)
    print("🔍 카카오 응답:", token_json)
    

    if "access_token" not in token_json:
        return JsonResponse(token_json, status=400)

    # ✅ 관리자 User에 강제 저장
    admin_user = User.objects.get(username="withjongseok@naver.com")
    
    # ✅ 토큰 저장 (모델 필드에 맞춤)
    if request.user.is_authenticated:
        KakaoToken.objects.update_or_create(
            user=admin_user,
            defaults={
                "access_token": token_json["access_token"],
                "refresh_token": token_json.get("refresh_token", ""),
                "expires_in": token_json.get("expires_in", 0),
                "refresh_token_expires_in": token_json.get("refresh_token_expires_in", 0),
            }
        )
    else:
        return JsonResponse({"error": "로그인한 사용자 없음"}, status=401)

    return JsonResponse({
        "message": "카카오 로그인 성공",
        "access_token": token_json["access_token"],
        "token_info": token_json,
    })

@login_required
def redirect_after_login(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')  # 관리자이면 관리자 대시보드로
    return redirect('home')  # 일반 유저는 홈

@staff_member_required
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

@staff_member_required
def approve_users(request):
    # 가입 승인 대기자
    inactive_users = User.objects.filter(is_active=False)

    # 회원탈퇴 요청자 (활성 계정이면서 탈퇴 요청한 경우)
    withdrawal_users = User.objects.filter(is_active=True, profile__withdrawal_requested=True)

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, "해당 사용자를 찾을 수 없습니다.")
            return redirect('approve_users')

        if action == 'approve':
            user.is_active = True
            user.save()
            messages.success(request, f'{user.first_name}님의 가입이 승인되었습니다.')

        elif action == 'reject':
            user.delete()
            messages.warning(request, f'{user.first_name}님의 가입이 거절되어 삭제되었습니다.')

        elif action == 'withdraw_approve':   # ✅ 회원탈퇴 승인
            user.delete()
            messages.success(request, f'{user.first_name}님의 회원탈퇴가 승인되었습니다.')

        return redirect('approve_users')

    return render(request, 'accounts/approve_users.html', {
        'inactive_users': inactive_users,
        'withdrawal_users': withdrawal_users,
    })

def check_username(request):
    username = request.GET.get('username', None)
    exists = User.objects.filter(username=username).exists()
    return JsonResponse({'exists': exists})

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def profile(request):
    user = request.user
    profile = getattr(user, "profile", None)  # 학부모/학생/강사
    institution_profile = getattr(user, "institution_profile", None)  # 기관

    if request.method == "POST":
        if profile and profile.user_type in ["parent", "student", "teacher"]:
            # ✅ 일반 회원(강사/학부모/학생) 업데이트
            user.first_name = request.POST.get("first_name", user.first_name)
            profile.user_type = request.POST.get("user_type", profile.user_type)
            profile.birth_date = request.POST.get("birth_date", profile.birth_date)
            profile.phone_number = request.POST.get("phone_number", profile.phone_number)
            profile.postcode = request.POST.get("postcode", profile.postcode)
            profile.address = request.POST.get("address", profile.address)
            profile.detail_address = request.POST.get("detail_address", profile.detail_address)

            user.save()
            profile.save()

        elif institution_profile:
            # ✅ 기관 회원 업데이트
            institution_profile.institution_name = request.POST.get("institution_name", institution_profile.institution_name)
            institution_profile.business_number = request.POST.get("business_number", institution_profile.business_number)
            institution_profile.contact_name = request.POST.get("contact_name", institution_profile.contact_name)
            institution_profile.contact_phone = request.POST.get("contact_phone", institution_profile.contact_phone)
            institution_profile.office_phone = request.POST.get("office_phone", institution_profile.office_phone)
            institution_profile.fax = request.POST.get("fax", institution_profile.fax)
            institution_profile.postcode = request.POST.get("postcode", institution_profile.postcode)
            institution_profile.address = request.POST.get("address", institution_profile.address)
            institution_profile.detail_address = request.POST.get("detail_address", institution_profile.detail_address)
            institution_profile.industry = request.POST.get("industry", institution_profile.industry)
            institution_profile.website = request.POST.get("website", institution_profile.website)
            institution_profile.note = request.POST.get("note", institution_profile.note)

            institution_profile.save()

        messages.success(request, "회원 정보가 성공적으로 수정되었습니다.")
        return redirect("profile")

    return render(request, "accounts/profile.html", {
        "user": user,
        "profile": profile,
        "institution_profile": institution_profile,
    })


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email  # 이메일을 username으로 설정
            user.is_active = False      # 관리자 승인 전까지 비활성화
            user.save()

            # ✅ Profile 생성
            profile = Profile.objects.create(
                user=user,
                user_type=form.cleaned_data['user_type'],
                birth_date=form.cleaned_data['birth_date'],
                phone_number=form.cleaned_data['phone_number'],
                postcode=form.cleaned_data['postcode'],
                address=form.cleaned_data['address'],
                detail_address=form.cleaned_data['detail_address'],
            )

            # ✅ 학부모일 경우 자녀 정보 저장
            if profile.user_type == "parent":
                child_names = request.POST.getlist("child_name[]")
                child_births = request.POST.getlist("child_birth[]")
                for name, birth in zip(child_names, child_births):
                    if name and birth:
                        Child.objects.create(
                            parent=profile,
                            name=name,
                            birth_date=birth
                        )

            # ✅ 가입 성공 메시지
            messages.success(request, "회원가입 신청이 완료되었습니다.\n관리자의 승인을 기다려주세요.")

            # ✅ 관리자에게 승인 요청 메일 보내기
            email = EmailMessage(
                subject='[사이트명] 새로운 회원 가입 승인 요청',
                body=f'새 가입 요청:\n이름: {user.first_name}\n이메일: {user.email}\n관리 페이지에서 승인해주세요.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=['robotmaking@naver.com'],
            )
            email.content_subtype = "plain"
            email.encoding = 'utf-8'
            email.send(fail_silently=True)

            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})

@login_required
def change_password(request):
    if request.method == "POST":
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)  # 비밀번호 변경 후 자동 로그인 유지
            messages.success(request, "비밀번호가 성공적으로 변경되었습니다.")
            return redirect('profile')
    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'accounts/change_password.html', {'form': form})

def is_admin(user):
    return user.is_staff  # 필요 시 .is_staff 로 변경 가능

@login_required
@user_passes_test(is_admin)
def admin_user_list(request):
    q = request.GET.get('q', '').strip()
    user_type = request.GET.get('user_type', '')
    status = request.GET.get('status', '')  # 'approved', 'pending', 'active', 'inactive'
    order = request.GET.get('order', '-date_joined')  # 정렬 키
    page = request.GET.get('page', 1)

    queryset = (
        User.objects.select_related('profile')
        .all()
        .order_by(order if order else '-date_joined')
    )

    if q:
        queryset = queryset.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
        )

    if user_type:
        queryset = queryset.filter(profile__user_type=user_type)

    if status == 'approved':
        queryset = queryset.filter(profile__is_approved=True)
    elif status == 'pending':
        queryset = queryset.filter(Q(profile__is_approved=False) | Q(profile__is_approved__isnull=True))
    elif status == 'active':
        queryset = queryset.filter(is_active=True)
    elif status == 'inactive':
        queryset = queryset.filter(is_active=False)

    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(page)

    context = {
        'page_obj': page_obj,
        'q': q,
        'user_type': user_type,
        'status': status,
        'order': order,
        'USER_TYPE_CHOICES': Profile.USER_TYPES,  # ✅ 여기에 모델 choices 그대로 전달
    }
    return render(request, 'accounts/admin_user_list.html', context)

@login_required
def request_withdrawal(request):
    profile = request.user.profile
    profile.withdrawal_requested = True
    profile.save()
    messages.success(request, "회원탈퇴 요청이 접수되었습니다. 관리자의 승인을 기다려주세요.")
    return redirect("profile")  # ✅ 'mypage' → 'profile'

# ✅ 학부모 전용 접근 제한
def is_parent(user):
    return hasattr(user, "profile") and user.profile.user_type == "parent"

@login_required
def parent_dashboard(request):
    """학부모 대시보드 안내 페이지"""
    return render(request, "accounts/parent_dashboard.html")

@login_required
def child_list(request):
    """자녀 관리 리스트 + 등록"""
    if not is_parent(request.user):
        return redirect("home")

    if request.method == "POST":
        form = ChildForm(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.parent = request.user.profile  # ✅ Profile 연결
            child.save()
            return redirect("child_list")
    else:
        form = ChildForm()

    children = Child.objects.filter(parent=request.user.profile)
    return render(request, "accounts/child_list.html", {"children": children, "form": form})

@login_required
def child_edit(request, pk):
    """자녀 수정"""
    child = get_object_or_404(Child, pk=pk, parent=request.user.profile)
    if request.method == "POST":
        form = ChildForm(request.POST, instance=child)
        if form.is_valid():
            form.save()
            return redirect("child_list")
    else:
        form = ChildForm(instance=child)
    return render(request, "accounts/child_form.html", {"form": form, "child": child})

@login_required
def child_delete(request, pk):
    """자녀 삭제"""
    child = get_object_or_404(Child, pk=pk, parent=request.user.profile)
    if request.method == "POST":
        child.delete()
        return redirect("child_list")
    return render(request, "accounts/child_confirm_delete.html", {"child": child})

def institution_signup(request):
    if request.method == 'POST':
        form = InstitutionSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "가입 신청이 접수되었습니다. 관리자 승인 후 이용 가능합니다.")
            return redirect('login')
        else:
            print("❌ 유효성 검사 실패:", form.errors)  # 🚨 콘솔에서 에러 확인
    else:
        form = InstitutionSignUpForm()
    return render(request, 'accounts/institution_signup.html', {'form': form})