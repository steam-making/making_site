from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import Child
from .models import Profile, InstitutionProfile

class CustomAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError("관리자의 승인이 필요합니다. 승인이 완료될 때까지 기다려주세요.", code='inactive')

class SignUpForm(UserCreationForm):
    email = forms.EmailField(label="이메일", required=True)
    # 기존 추가 필드 유지
    user_type = forms.ChoiceField(
        label='회원 유형',
        choices=[
            ('student', '학생'), 
            ('parent', '학부모'), 
            ('pre_teacher', '예비강사'),
            ('teacher', '강사')
            ]
        )
    birth_date = forms.DateField(label='생년월일', widget=forms.DateInput(attrs={'type': 'date'}))
    phone_number = forms.CharField(label='전화번호')
    postcode = forms.CharField(label='우편번호', required=False)
    address = forms.CharField(label='주소', required=False)
    detail_address = forms.CharField(label='상세주소', required=False)
    first_name = forms.CharField(label='이름', max_length=30, required=True)

    class Meta:
        model = User
        fields = ['first_name','email', 'password1', 'password2',
                'user_type', 'birth_date', 'phone_number',
                'postcode', 'address', 'detail_address']

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("이미 사용 중인 이메일입니다.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # username에 이메일 저장
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']  # ✅ 이름 저장
        user.is_active = False  # ✅ 가입 즉시 비활성화 (승인 전 로그인 불가)
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(label="이메일", required=True)

    class Meta:
        model = User
        fields = ['username', 'email']
        
class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(label="현재 비밀번호", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(label="새 비밀번호", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(label="새 비밀번호 확인", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ["name", "birth_date"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "자녀 이름"}),
            "birth_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }    
        
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, InstitutionProfile


class InstitutionSignUpForm(UserCreationForm):
    # 계정
    email = forms.EmailField(label="기관 이메일", required=True)

    # 기관 정보
    institution_name = forms.CharField(label="기관명", max_length=120)
    business_number  = forms.CharField(label="사업자등록번호", max_length=30, required=False)
    contact_name     = forms.CharField(label="담당자명", max_length=60)

    # 연락처
    office_phone   = forms.CharField(label="기관 전화번호", max_length=30, required=False)
    contact_phone  = forms.CharField(label="담당자 휴대폰 번호", max_length=30, required=False)
    fax            = forms.CharField(label="팩스", max_length=30, required=False)

    # 주소
    postcode       = forms.CharField(label="우편번호", required=False)
    address        = forms.CharField(label="주소", required=False)
    detail_address = forms.CharField(label="상세주소", required=False)

    # 추가
    industry = forms.CharField(label="업종", max_length=60, required=False)
    website  = forms.URLField(label="홈페이지", required=False)
    note     = forms.CharField(label="비고", widget=forms.Textarea, required=False)

    class Meta:
        model = User
        fields = [
            'institution_name', 'email', 'password1', 'password2',
            'business_number', 'contact_name',
            'office_phone', 'contact_phone', 'fax',
            'postcode', 'address', 'detail_address',
            'industry', 'website', 'note',
        ]

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("이미 사용 중인 이메일입니다.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['institution_name']  # 기관명
        user.is_active = False
        if commit:
            user.save()
            # ✅ Profile 생성 (기관 유형, 담당자 휴대폰 저장)
            Profile.objects.create(
                user=user,
                user_type='institution',
                phone_number=self.cleaned_data.get('contact_phone', ''),  # ✅ contact_phone 사용
                birth_date=None
            )
            # ✅ InstitutionProfile 생성
            InstitutionProfile.objects.create(
                user=user,
                institution_name=self.cleaned_data['institution_name'],
                business_number=self.cleaned_data.get('business_number', ''),
                contact_name=self.cleaned_data['contact_name'],
                office_phone=self.cleaned_data.get('office_phone', ''),
                contact_phone=self.cleaned_data.get('contact_phone', ''),   # ✅ contact_phone 사용
                fax=self.cleaned_data.get('fax', ''),
                postcode=self.cleaned_data.get('postcode', ''),
                address=self.cleaned_data.get('address', ''),
                detail_address=self.cleaned_data.get('detail_address', ''),
                industry=self.cleaned_data.get('industry', ''),
                website=self.cleaned_data.get('website', ''),
                note=self.cleaned_data.get('note', ''),
            )
        return user






