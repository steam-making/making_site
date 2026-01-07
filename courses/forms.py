from django import forms
from .models import LearningProgram, Program, ProgramApplication
from .models import InstitutionReservation, ProgramProduct, ProductMaterial
from .models import Category
import json
import os
from accounts.models import Profile
from django.core.exceptions import ValidationError
from .models import Target
from django.core.files.storage import default_storage
from django.forms import inlineformset_factory
import datetime
from .models import CurriculumProgram, CurriculumSyllabus

class CurriculumSyllabusExcelForm(forms.Form):
    excel_file = forms.FileField(
        label="차시 엑셀 파일",
        widget=forms.FileInput(attrs={
            "class": "form-control",
            "accept": ".xlsx,.xls"
        })
    )


class CurriculumProgramForm(forms.ModelForm):
    class Meta:
        model = CurriculumProgram
        fields = ["name", "description", "target_start", "target_end"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "target_start": forms.Select(attrs={"class": "form-select"}),
            "target_end": forms.Select(attrs={"class": "form-select"}),
        }

class CurriculumSyllabusForm(forms.ModelForm):
    class Meta:
        model = CurriculumSyllabus
        fields = ["week", "title", "content", "material"]
        widgets = {
            "week": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1
            }),
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "예: 로봇의 움직임 이해하기"
            }),
            "content": forms.Textarea(attrs={
                "rows": 5,
                "class": "form-control"
            }),
            "material": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "예: 로봇 키트, 태블릿"
            }),
        }



class LearningProgramForm(forms.ModelForm):
    class Meta:
        model = LearningProgram
        fields = ["name", "description", "image"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

class ProgramAdminForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = "__all__"
        widgets = {
            "tuition": forms.TextInput(attrs={"class": "vTextField"})
        }

    def clean_tuition(self):
        val = self.cleaned_data.get("tuition", "")
        if isinstance(val, str):
            val = val.replace(",", "").strip()
        return int(val) if val else 0

# 프로그램 등록/수정 폼
from django import forms
from .models import Program
from accounts.models import Profile  # 강사 필터링 위해 import

from django import forms
from .models import Program
from accounts.models import Profile

class ProgramForm(forms.ModelForm):
    tuition = forms.CharField(
        label="수업료",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_tuition"}),
        initial="120,000",
    )

    curriculum_program = forms.ModelChoiceField(
        queryset=CurriculumProgram.objects.all(),
        label="커리큘럼 프로그램 선택",
        required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = Program
        fields = [
            "name", "curriculum_program", "target_start", "target_end", "teacher",
            "recruit_type",   # ⬅ 반드시 앞쪽으로!
            "recruit_start_date", "recruit_end_date",
            "start_date", "end_date", "class_duration",
            "weekly_sessions", "monthly_sessions", "months", "session_count",
            "tuition", "base_fee", "material_fee", "include_materials",
            "material", "image", "status",
            "description", "program_types",
        ]
        widgets = {
            "target_start": forms.Select(attrs={"class": "form-select", "id": "id_target_start"}),
            "target_end": forms.Select(attrs={"class": "form-select", "id": "id_target_end"}),
            "teacher": forms.Select(attrs={"class": "form-select"}),
            "recruit_start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "recruit_end_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "class_duration": forms.NumberInput(attrs={"class": "form-control"}),
            "program_types": forms.CheckboxSelectMultiple(),

            # ⬅ 추가: recruit_type의 widget을 명확히 지정
            "recruit_type": forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["teacher"].queryset = Profile.objects.filter(
            user_type="center_teacher"
        ).select_related("user")
        self.fields["teacher"].label_from_instance = (
            lambda obj: obj.user.get_full_name() or obj.user.username
        )
        self.fields["teacher"].empty_label = "미지정"

        if "image" in self.fields:
            self.fields["image"].widget.clear_checkbox_label = "삭제"

        if self.instance and self.instance.tuition:
            self.initial["tuition"] = f"{self.instance.tuition:,}"
        elif not self.initial.get("tuition"):
            self.initial["tuition"] = "120,000"

    def clean_class_days(self):
        # JSONField인 경우 리스트 반환
        return self.cleaned_data.get("class_days", [])

    def clean_tuition(self):
        tuition = self.cleaned_data.get("tuition")
        if tuition:
            if isinstance(tuition, str):
                tuition = tuition.replace(",", "").strip()
            try:
                return int(tuition)
            except ValueError:
                raise forms.ValidationError("숫자만 입력하세요.")
        return 0

from .models import ProgramClass, Program

class ProgramClassForm(forms.ModelForm):
    DAYS_OF_WEEK = Program.DAYS_OF_WEEK

    # ✅ 여러 요일 선택 (hidden input, JS에서 하나만 value="mon,wed"로 관리)
    days = forms.MultipleChoiceField(
        choices=Program.DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple,   # 또는 HiddenInput + JS 관리
        required=False,
        label="요일"
    )

    class Meta:
        model = ProgramClass
        fields = ["id", "days", "start_time", "end_time", "start_date", "end_date","capacity"]
        widgets = {
            "start_time": forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
            "end_time": forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
            "start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "capacity": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk:  # 새 반일 때
            self.fields["capacity"].initial = 10
            
        # ✅ DB 값이 문자열("mon,wed")이면 리스트로 변환해 체크박스 초기값 세팅
        if self.instance and self.instance.days:
            if isinstance(self.instance.days, str):
                self.fields["days"].initial = self.instance.days.split(",")

        # ✅ 새 폼일 때 기본값
        if not self.instance.pk:
            self.fields["start_time"].initial = datetime.time(10, 0)  # 오전 10:00
            self.fields["end_time"].initial = datetime.time(11, 0)   # 기본 1시간 뒤 예시

    def clean_days(self):
        value = self.cleaned_data.get("days", [])
        if isinstance(value, str):
            # 혹시 문자열이 들어오면 split
            return [d for d in value.split(",") if d]
        return value or []

    
from django.forms import inlineformset_factory
from .models import Program, ProgramClass

# 새 등록 시 기본 1개
ProgramClassFormSetCreate = inlineformset_factory(
    Program,
    ProgramClass,
    form=ProgramClassForm,
    extra=1,        # ✅ 기본 1개
    can_delete=True
)

# 수정 시 기존 데이터만
ProgramClassFormSetEdit = inlineformset_factory(
    Program,
    ProgramClass,
    form=ProgramClassForm,
    extra=0,        # ✅ 빈 행 없음
    can_delete=True
)

# 수강신청 폼
class ProgramApplicationForm(forms.ModelForm):
    applicant_name = forms.CharField(
        label="신청자명",
        required=False,  # ✅ 부모 계정일 땐 비워도 통과
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "신청자명"})
    )
    phone = forms.CharField(
        label="연락처",
        required=False,  # ✅ 부모 계정일 땐 비워도 통과
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "연락처(숫자만 또는 하이픈 포함)"})
    )
    memo = forms.CharField(
        label="요청사항(선택)",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "요청사항(선택)"})
    )

    class Meta:
        model = ProgramApplication
        fields = ["applicant_name", "phone", "memo"]

from django import forms
from django.contrib.auth.models import User
from .models import InstitutionReservation, ProgramProduct

class InstitutionReservationForm(forms.ModelForm):
    # ✅ 10:00 ~ 19:30, 30분 단위 선택지 생성
    TIME_CHOICES = [
        (f"{h:02d}:{m:02d}", f"{h:02d}:{m:02d}")
        for h in range(10, 20)   # 10시 ~ 19시
        for m in (0, 30)
        if not (h == 19 and m == 60)  # 19:30 포함
    ]

    start_time = forms.ChoiceField(
        choices=TIME_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="시작 시간"
    )
    
    class Meta:
        model = InstitutionReservation
        fields = ["institution", "product", "selected_topic", "date", "start_time", "end_time", "headcount", "place", "memo"]
        widgets = {
            "institution": forms.Select(attrs={"class": "form-select"}),
            "product": forms.Select(attrs={"class": "form-select", "id": "id_product"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-control", "id": "id_start_time"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": "form-control", "id": "id_end_time", "readonly": "readonly"}),
            "headcount": forms.NumberInput(attrs={"class": "form-control", "id": "id_headcount", "min": 1}),
            "place": forms.Textarea(attrs={"class": "form-control","rows": 2}),
            "memo": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "selected_topic": forms.TextInput(attrs={"class": "form-control", "placeholder": "예: 3D펜 로봇 만들기"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        from django.contrib.auth.models import User
        qs = User.objects.filter(profile__user_type="institution")

        # ✅ 드롭다운에 기관명 출력
        self.fields["institution"].queryset = qs
        self.fields["institution"].label_from_instance = (
            lambda obj: obj.institution_profile.institution_name if hasattr(obj, "institution_profile") else obj.username
        )
        self.fields["institution"].widget.attrs.update({"class": "form-select"})

        # ✅ 기관 로그인한 경우 자기 자신만 선택되도록
        if user and hasattr(user, "profile") and user.profile.user_type == "institution":
            self.fields["institution"].initial = user
            self.fields["institution"].disabled = True

        # ✅ 프로그램 필드
        self.fields["product"].widget.attrs.update({"class": "form-select"})

        self.fields["headcount"].widget.attrs.update({"class": "form-control"})
        self.fields["place"].widget.attrs.update({"class": "form-control"})

class CustomClearableFileInput(forms.ClearableFileInput):
    clear_checkbox_label = '삭제'  # ✅ 기본 "Clear" → "삭제" 로 변경
        
class ProgramProductForm(forms.ModelForm):
    class Meta:
        model = ProgramProduct
        fields = '__all__'
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "프로그램명을 입력하세요"}),
            "category": forms.Select(attrs={"class": "form-select"}),  # ✅ TextInput → Select로 변경
            "duration_minutes": forms.NumberInput(attrs={"class": "form-control", "min": 10, "step": 5}),
            "base_price": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": 1000}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "설명"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "topics": forms.HiddenInput(),  # ✅ 주제는 JS에서 동적으로 처리
            "status": forms.Select(attrs={"class": "form-select"}),
            "included_materials": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }   
    
    def clean_image(self):
        """
        이미지 업로드 시 같은 파일명이 이미 존재하면
        새로 업로드하지 않고 기존 파일을 그대로 사용.
        """
        image = self.cleaned_data.get("image")
        if image:
            filename = os.path.basename(image.name)
            upload_path = os.path.join("products", filename)

            # 이미 서버에 같은 파일명이 있는 경우 → 업로드 막는 대신 기존 파일을 참조
            if default_storage.exists(upload_path):
                # 폼의 image 필드 값을 기존 경로로 덮어쓰기
                self.cleaned_data["image"] = upload_path
                return upload_path

        return image
        
    def clean_topics(self):
            data = self.cleaned_data["topics"]
            if isinstance(data, str):  # 문자열이면 JSON 파싱
                try:
                    return json.loads(data)
                except Exception:
                    return []
            return data 

# ✅ 재료 입력용 Formset
ProductMaterialFormSet = inlineformset_factory(
    ProgramProduct,
    ProductMaterial,
    fields=["name", "price"],
    extra=1,
    can_delete=True,
    widgets={
        "name": forms.TextInput(attrs={"class": "form-control"}),
        "price": forms.NumberInput(attrs={"class": "form-control"}),
    }
)   

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "카테고리명 입력"}),
        }
        

class TargetForm(forms.ModelForm):
    class Meta:
        model = Target
        fields = ["code", "name", "age"]
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "age": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }     

class SyllabusUploadForm(forms.Form):
    excel_file = forms.FileField(
        label="수업계획서 엑셀 파일",
        widget=forms.FileInput(
            attrs={"class": "form-control"}
        )
    )

# ✅ 실제 수강생 등록용 Form (관리자 전용)

from .models import ProgramEnrollment
from accounts.models import Child

class ProgramEnrollmentForm(forms.ModelForm):
    student = forms.ModelChoiceField(
        queryset=Child.objects.all(),
        label="학생 선택",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = ProgramEnrollment
        fields = ["student"]
