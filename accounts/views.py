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
from django.views.decorators.http import require_POST

from django.urls import reverse

def kakao_login(request):
    client_id = settings.KAKAO_REST_API_KEY
    # 현재 접속 중인 도메인을 기반으로 리다이렉트 URI 생성
    redirect_uri = request.build_absolute_uri(reverse('kakao_callback'))
    
    kakao_auth_url = (
        f"https://kauth.kakao.com/oauth/authorize?"
        f"client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=talk_message,friends"
    )
    return redirect(kakao_auth_url)

def kakao_callback(request):
    code = request.GET.get("code")
    if not code:
        return HttpResponse("인가 코드가 없습니다.", status=400)

    # 1. 토큰 요청
    token_url = "https://kauth.kakao.com/oauth/token"
    redirect_uri = request.build_absolute_uri(reverse('kakao_callback'))
    
    data = {
        "grant_type": "authorization_code",
        "client_id": settings.KAKAO_REST_API_KEY,
        "redirect_uri": redirect_uri,
        "code": code,
    }
    res = requests.post(token_url, data=data)
    token_json = res.json()

    if "access_token" not in token_json:
        return JsonResponse(token_json, status=400)

    access_token = token_json["access_token"]

    # 2. 사용자 정보 요청
    user_info_url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_res = requests.get(user_info_url, headers=headers)
    user_info = user_res.json()

    kakao_id = str(user_info.get("id"))
    kakao_account = user_info.get("kakao_account", {})
    email = kakao_account.get("email")
    nickname = kakao_account.get("profile", {}).get("nickname", "")

    # 3. 로그인/연동/가입 로직
    if request.user.is_authenticated:
        # 로그인 상태: 현재 계정에 카카오 연동
        # ⚠️ 이미 다른 계정에 연동된 카카오 ID인지 확인
        existing_profile = Profile.objects.filter(kakao_id=kakao_id).exclude(user=request.user).first()
        if existing_profile:
            messages.error(request, f"이 카카오 계정은 이미 다른 사용자({existing_profile.user.username})에게 연동되어 있습니다.")
            return redirect("profile")

        profile, created = Profile.objects.get_or_create(user=request.user)
        profile.kakao_id = kakao_id
        profile.kakao_name = nickname # ✅ 카카오 닉네임 저장
        profile.save()
        
        # 토큰 저장
        KakaoToken.objects.update_or_create(
            user=request.user,
            defaults={
                "access_token": token_json["access_token"],
                "refresh_token": token_json.get("refresh_token", ""),
                "expires_in": token_json.get("expires_in", 0),
                "refresh_token_expires_in": token_json.get("refresh_token_expires_in", 0),
            }
        )
        messages.success(request, "카카오 계정이 연동되었습니다.")
        return redirect("profile")

    else:
        # 비로그인 상태: 로그인 또는 가입 처리
        profile = Profile.objects.filter(kakao_id=kakao_id).first()
        
        if not profile and email:
            # 카카오 ID는 없지만 이메일이 일치하는 사용자가 있는 경우 자동 연동
            user = User.objects.filter(email=email).first()
            if user:
                profile, created = Profile.objects.get_or_create(user=user)
                profile.kakao_id = kakao_id
                profile.kakao_name = nickname # ✅ 카카오 닉네임 저장
                profile.save()

        if profile:
            # 기존 사용자 로그인
            login(request, profile.user)
            
            # 토큰 저장
            KakaoToken.objects.update_or_create(
                user=profile.user,
                defaults={
                    "access_token": token_json["access_token"],
                    "refresh_token": token_json.get("refresh_token", ""),
                    "expires_in": token_json.get("expires_in", 0),
                    "refresh_token_expires_in": token_json.get("refresh_token_expires_in", 0),
                }
            )
            messages.success(request, f"{profile.user.first_name or profile.user.username}님, 환영합니다!")
            return redirect("home")
        else:
            # 신규 가입 처리 (임시)
            # 닉네임과 이메일을 기반으로 유저 생성
            username = email if email else f"kakao_{kakao_id}"
            if User.objects.filter(username=username).exists():
                username = f"{username}_{kakao_id[:5]}"
            
            user = User.objects.create_user(
                username=username,
                email=email if email else "",
                first_name=nickname,
                is_active=False # 관리자 승인 대기
            )
            Profile.objects.create(user=user, kakao_id=kakao_id, kakao_name=nickname)
            
            # 토큰 저장
            KakaoToken.objects.update_or_create(
                user=user,
                defaults={
                    "access_token": token_json["access_token"],
                    "refresh_token": token_json.get("refresh_token", ""),
                    "expires_in": token_json.get("expires_in", 0),
                    "refresh_token_expires_in": token_json.get("refresh_token_expires_in", 0),
                }
            )
            messages.success(request, "카카오 계정으로 가입 신청이 완료되었습니다. 관리자 승인 후 이용 가능합니다.")
            return redirect("login")

@login_required
@require_POST
def kakao_unlink(request):
    """카카오 계정 연동 해제"""
    profile = getattr(request.user, 'profile', None)
    if profile:
        profile.kakao_id = None
        profile.kakao_name = None
        profile.save()
        
        # 관련 토큰 삭제
        KakaoToken.objects.filter(user=request.user).delete()
        
        messages.success(request, "카카오 계정 연동이 해제되었습니다.")
    return redirect("profile")

@login_required
def redirect_after_login(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    profile = getattr(request.user, "profile", None)
    user_type = getattr(profile, "user_type", "")

    if user_type in ["teacher", "center_teacher"]:
        return redirect('teacher_dashboard')
    if user_type == "parent":
        return redirect('parent_dashboard')

    return redirect('home')

@staff_member_required
def admin_dashboard(request):
    from teachers.models import TeachingInstitution
    from materials.models import Material, MaterialRelease, Vendor, VendorType
    from django.contrib.auth.models import User
    from django.db.models import Count, Q
    
    # ✅ 주요 통계 데이터
    # 회원 통계
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    pending_users = User.objects.filter(is_active=False).count()
    teachers = User.objects.filter(profile__user_type='teacher').count()
    center_teachers = User.objects.filter(profile__user_type='center_teacher').count()
    
    # 기관/장소 통계
    total_institutions = TeachingInstitution.objects.count()
    active_institutions = TeachingInstitution.objects.filter(is_closed=False).count()
    
    # 교구재 통계
    total_materials = Material.objects.count()
    total_vendors = Vendor.objects.count()
    total_vendor_types = VendorType.objects.count()
    
    # 출고/주문 통계
    total_releases = MaterialRelease.objects.count()
    unpaid_releases = MaterialRelease.objects.filter(payment_status='unpaid').count()
    paid_releases = MaterialRelease.objects.filter(payment_status='paid').count()
    
    # ✅ 최근 활동 (최근 7일)
    recent_releases = MaterialRelease.objects.order_by('-created_at')[:5]
    
    context = {
        # 회원
        'total_users': total_users,
        'active_users': active_users,
        'pending_users': pending_users,
        'teachers': teachers,
        'center_teachers': center_teachers,
        # 기관
        'total_institutions': total_institutions,
        'active_institutions': active_institutions,
        # 교구재
        'total_materials': total_materials,
        'total_vendors': total_vendors,
        'total_vendor_types': total_vendor_types,
        # 출고
        'total_releases': total_releases,
        'unpaid_releases': unpaid_releases,
        'paid_releases': paid_releases,
        # 최근 활동
        'recent_releases': recent_releases,
    }
    
    return render(request, 'admin_dashboard.html', context)

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
    order = request.GET.get('order', '-date_joined')
    page = request.GET.get('page', 1)

    queryset = (
        User.objects.select_related('profile')
        .all()
        .order_by(order)
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

    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(page)

    context = {
        'page_obj': page_obj,
        'q': q,
        'user_type': user_type,
        'order': order,
        'USER_TYPE_CHOICES': Profile.USER_TYPES,
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

@staff_member_required
@require_POST
def admin_user_activate(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse({"success": False, "error": "user_not_found"})

    user.is_active = True
    user.save(update_fields=["is_active"])

    return JsonResponse({"success": True})

@staff_member_required
@require_POST
def admin_user_bulk_create(request):
    emails = request.POST.getlist("email[]")
    names = request.POST.getlist("first_name[]")
    types = request.POST.getlist("user_type[]")
    passwords = request.POST.getlist("password[]")

    created = 0

    for email, name, utype, pw in zip(emails, names, types, passwords):
        if not email:
            continue

        if User.objects.filter(username=email).exists():
            continue

        user = User.objects.create_user(
            username=email,
            email=email,
            password=pw or "m123456*",
            first_name=name,
            is_active=True,
        )

        Profile.objects.create(
            user=user,
            user_type=utype
        )

        created += 1

    messages.success(request, f"{created}명 회원이 등록되었습니다.")
    return redirect("admin_user_list")


@staff_member_required
@require_POST
def admin_user_bulk_update_type(request):
    raw_ids = request.POST.getlist("user_ids[]")
    new_type = request.POST.get("user_type", "").strip()

    valid_types = {value for value, _label in Profile.USER_TYPES}
    if new_type not in valid_types:
        return JsonResponse({"success": False, "error": "invalid_user_type"}, status=400)

    user_ids = []
    for raw_id in raw_ids:
        try:
            user_id = int(raw_id)
        except (TypeError, ValueError):
            continue

        if user_id > 0:
            user_ids.append(user_id)

    if not user_ids:
        return JsonResponse({"success": False, "error": "no_users_selected"}, status=400)

    unique_user_ids = list(set(user_ids))
    updated_count = Profile.objects.filter(user_id__in=unique_user_ids).update(user_type=new_type)
    skipped_count = max(len(unique_user_ids) - updated_count, 0)

    return JsonResponse(
        {
            "success": True,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
        }
    )

