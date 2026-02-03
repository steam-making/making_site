from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import Profile, Child
from django.conf import settings

class Subject(models.Model):
    name = models.CharField("수업 분야명", max_length=100, unique=True)

    class Meta:
        verbose_name = "수업 분야"
        verbose_name_plural = "수업 분야 목록"

    def __str__(self):
        return self.name

class CurriculumProgram(models.Model):
    CLASS_TYPE_CHOICES = [
        ("정규반", "정규반"),
        ("단기특강", "단기특강"),
        ("체험형", "체험형"),
    ]

    DIFFICULTY_CHOICES = [
        ("intro", "입문"),
        ("basic", "기초"),
        ("intermediate", "중급"),
        ("advanced", "심화"),
    ]

    name = models.CharField("커리큘럼 프로그램명", max_length=200)
    description = models.TextField("프로그램 소개", blank=True)

    duration_minutes = models.PositiveIntegerField("수업시간(분)", null=True, blank=True, help_text="분 단위")
    duration_period = models.CharField("수업기간", max_length=100, blank=True, help_text="예: 12주, 1개월")
    class_type = models.CharField("수업 유형", max_length=20, choices=CLASS_TYPE_CHOICES, blank=True)
    difficulty_level = models.CharField("난이도", max_length=20, choices=DIFFICULTY_CHOICES, blank=True)
    subjects = models.ManyToManyField(Subject, verbose_name="수업 분야", blank=True)

    target_start = models.ForeignKey(
        "Target",
        on_delete=models.PROTECT,
        related_name="curriculum_programs_start",
        null=True,
        blank=True
    )
    target_end = models.ForeignKey(
        "Target",
        on_delete=models.PROTECT,
        related_name="curriculum_programs_end",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    

class CurriculumSyllabus(models.Model):
    program = models.ForeignKey(
        CurriculumProgram,
        on_delete=models.CASCADE,
        related_name="syllabus",
        null=True,      # ⭐ 임시로 True
        blank=True 
    )
    week = models.PositiveIntegerField("차시")
    title = models.CharField("수업 주제", max_length=200)
    content = models.TextField("수업 내용")
    material = models.CharField("준비물", max_length=200, blank=True)

    class Meta:
        ordering = ["week"]

STATUS_CHOICES = [
    ("open", "모집중"),
    ("closed", "모집마감"),
    ("hidden", "비공개"),
]

class LearningProgram(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # 이미지 필드
    image = models.ImageField(upload_to="learning_programs/", blank=True, null=True)

    program_type = models.ForeignKey(
        "ProgramType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="learning_programs",
        verbose_name="프로그램 유형"
    )

    def get_url(self):
        return reverse("course_home", args=[self.id])

    def __str__(self):
        return self.name


class Chapter(models.Model):
    program = models.ForeignKey(LearningProgram, on_delete=models.CASCADE)
    number = models.PositiveIntegerField()  # 1, 2, 3...
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"{self.number}장 - {self.title}"


class Item(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    number = models.PositiveIntegerField(default=1)  # 차시 내 항목 순서
    key = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    item_type = models.CharField(max_length=50)  # example/problem/project/homework
    explain_html = models.TextField(blank=True, null=True)
    hint = models.TextField(blank=True, null=True)
    answer_code = models.TextField(blank=True, null=True)
    expected_output = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["chapter", "number"]

    def __str__(self):
        return f"{self.chapter.number}장 - {self.title}"

class UserProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    code = models.TextField(blank=True)
    last_output = models.TextField(blank=True)
    score = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'item')

class LearningEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    program = models.ForeignKey(LearningProgram, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)


class ProgramType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    order = models.PositiveIntegerField(default=0)   # 정렬 순서

    class Meta:
        ordering = ['order', 'name']   # 🔥 추가해야 정렬 제대로 됨
        verbose_name = "프로그램 유형"
        verbose_name_plural = "프로그램 유형 목록"

    def __str__(self):
        return self.name


class Target(models.Model):
    code = models.CharField(max_length=20, unique=True, blank=True)
    name = models.CharField(max_length=50, unique=True)
    age = models.PositiveIntegerField("기준 나이", null=True, blank=True)  # 예: 8
    
    class Meta:
        verbose_name = "대상"
        verbose_name_plural = "대상 목록"
        ordering = ["id"]   # ✅ code 순서대로 정렬되게 설정

    def __str__(self):
        return f"{self.name} ({self.age}세)" if self.age else self.name
    



class ProgramSyllabus(models.Model):
    program = models.ForeignKey(
        "Program",
        on_delete=models.CASCADE,
        related_name="syllabus"
    )
    week = models.PositiveIntegerField("차시")
    title = models.CharField("수업 주제", max_length=200)
    content = models.TextField("수업 내용")
    material = models.CharField("준비물", max_length=200, blank=True)
    note = models.CharField("비고", max_length=200, blank=True)

    class Meta:
        ordering = ["week"]

    def __str__(self):
        return f"{self.program.name} - {self.week}차시"

class Program(models.Model):
    RECRUIT_TYPE_CHOICES = [
        ('always', '상시모집'),
        ('event', '이벤트'),
        ('short', '단기수업'),
    ]

    # 기존 데이터 때문에 null=True, blank=True 필수!
    recruit_type = models.CharField(
        max_length=20,
        choices=RECRUIT_TYPE_CHOICES,
        null=True,
        blank=True,
        default='always'  # 새로 등록되는 건 기본값 상시모집
    )

    name = models.CharField("프로그램명", max_length=200)
    target_start = models.ForeignKey("Target", on_delete=models.PROTECT, related_name="programs_start", null=True, blank=True)
    target_end = models.ForeignKey("Target", on_delete=models.PROTECT, related_name="programs_end", null=True, blank=True)

    # ✅ 유형 선택 (FK)
    program_types = models.ManyToManyField(ProgramType, blank=True)

    # ✅ 교구재: 그냥 입력
    material = models.CharField(max_length=100, blank=True, help_text="예: 없음, 대여, 보유")
    
    # ✅ 담당 강사 (홈페이지 가입된 강사만 선택 가능, 옵션)
    teacher = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'user_type': 'center_teacher'},
        verbose_name="담당 강사"
    )

    # ✅ 모집기간
    recruit_start_date = models.DateField("모집 시작일", null=True, blank=True)
    recruit_end_date = models.DateField("모집 마감일", null=True, blank=True)

    # ✅ 수업기간
    start_date = models.DateField("수업 시작일", null=True, blank=True)
    end_date = models.DateField("수업 종료일", null=True, blank=True) 

    # ✅ 수업 요일/시간/정원
    DAYS_OF_WEEK = [
        ("mon", "월"), ("tue", "화"), ("wed", "수"), ("thu", "목"),
        ("fri", "금"), ("sat", "토"), ("sun", "일"),
    ]
    class_duration = models.PositiveIntegerField("수업시간(분)", default=60, help_text="분 단위로 입력하세요")

    weekly_sessions = models.PositiveIntegerField("주 횟수", default=0)     # 주 몇 회
    monthly_sessions = models.PositiveIntegerField("월 횟수", default=0)    # 자동계산: 주 × 4
    months = models.PositiveIntegerField("개월 과정", default=0)            # 과정 개월 수
    session_count = models.PositiveIntegerField("수업횟수", null=True, blank=True)
    
    
    description = models.TextField("상세내용", blank=True)
    image = models.ImageField("대표이미지", upload_to="courses/", blank=True, null=True)
    status = models.CharField("상태", max_length=20, choices=STATUS_CHOICES, default="hidden")
    created_at = models.DateTimeField(auto_now_add=True)
    
    base_fee = models.PositiveIntegerField("강사료", default=0)        # 강사료 / 기본 수강료
    material_fee = models.PositiveIntegerField("교구비", default=0)   # 교구재 비용
    include_materials = models.BooleanField("교구재 포함", default=False)
    tuition = models.PositiveIntegerField("수강료(월)", default=120000, null=True, blank=True)     # 최종 월 수업료

    curriculum_program = models.ForeignKey(
        CurriculumProgram,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="programs",
        verbose_name="연결 커리큘럼 프로그램"
    )


    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
    
    def get_target_range(self):
        if not self.target_start and not self.target_end:
            return "(대상 없음)"
        if self.target_start and not self.target_end:
            return self.target_start.name
        if not self.target_start and self.target_end:
            return self.target_end.name

        # 둘 다 있는 경우
        if self.target_start == self.target_end:
            return self.target_start.name
        return f"{self.target_start.name}~{self.target_end.name}"


    def get_class_days_display(self):
        """저장된 요일 코드 → 한글로 변환"""
        if not self.class_days:
            return ""
        code_map = dict(self.DAYS_OF_WEEK)
        return ", ".join([code_map.get(day, day) for day in self.class_days.split(",") if day])
    
    # ✅ 현재 신청자 수
    def current_applicants(self):
        return self.applications.filter(status__in=["pending", "approved"]).count()
    
    def current_students(self):
        return self.enrollments.filter(is_active=True).count()
    
    # ✅ 총 수업횟수 자동 계산
    def calculate_session_count(self):
        if self.months == 0:
            return 0
        self.monthly_sessions = self.weekly_sessions * 4
        return self.monthly_sessions * self.months
    
    def get_schedule_summary(self):
        """예: 주1회 월4회 60분"""
        weekly = f"주{self.weekly_sessions}회" if self.weekly_sessions else ""
        monthly = f"월{self.monthly_sessions}회" if self.monthly_sessions else ""
        duration = f"{self.class_duration}분" if self.class_duration else ""
        return " ".join(filter(None, [weekly, monthly, duration]))
    
    def save(self, *args, **kwargs):
        # 저장 시 session_count 자동 계산
        self.session_count = self.calculate_session_count()
        super().save(*args, **kwargs)


from django.db import models

class ProgramClass(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="classes")
    name = models.CharField("반 이름", max_length=100)
    days = models.JSONField("요일들", default=list, blank=True)   # ✅ 여러 요일
    start_time = models.TimeField("시작 시간")
    end_time = models.TimeField("종료 시간")
    start_date = models.DateField("수업 시작일")
    end_date = models.DateField("수업 종료일", null=True, blank=True)
    order = models.PositiveIntegerField("순서", default=1)
    capacity = models.PositiveIntegerField("정원", default=10)

# courses/models.py

class ProgramApplication(models.Model):
    STATUS = [
        ("pending", "신청접수"),
        ("approved", "승인"),
        ("rejected", "반려"),
        ("cancelled", "취소"),
    ]

    program = models.ForeignKey("Program", on_delete=models.CASCADE, related_name="applications")
    program_class = models.ForeignKey(
        "ProgramClass",
        on_delete=models.CASCADE,
        related_name="applications",
        null=True,
        blank=True
    )
    applicant = models.ForeignKey(
        "accounts.Profile",
        on_delete=models.CASCADE,
        related_name="program_applications",
        null=True,
        blank=True
    )
    child = models.ForeignKey(
        "accounts.Child",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applications"
    )
    applicant_name = models.CharField("신청자명", max_length=100)
    phone = models.CharField("연락처", max_length=30)
    memo = models.CharField("요청사항(선택)", max_length=300, blank=True)
    status = models.CharField("상태", max_length=20, choices=STATUS, default="pending")
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        
        constraints = [
            models.UniqueConstraint(
                fields=["program", "program_class", "child"],
                name="unique_program_class_child"
            )
        ]
        ordering = ["-applied_at"]

    def __str__(self):
        base = f"{self.program.name}"
        if self.program_class:
            base += f" - {self.program_class.name}"
        if self.child:
            return f"{base} - {self.child.name} (부모:{self.applicant.user.username if self.applicant else ''})"
        return f"{base} - {self.applicant.user.username if self.applicant else ''}"


from accounts.models import Profile

class ProgramEnrollment(models.Model):
    """
    ✅ 실제 수강생 (회원 기준)
    - 관리자 직접 등록
    - 신청 승인 후 자동 등록
    """

    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="프로그램"
    )

    program_class = models.ForeignKey(
        ProgramClass,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="반"
    )

    # 🔥 핵심 변경: Child → Profile
    student = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="program_enrollments",
        limit_choices_to={"user_type": "student"},
        verbose_name="학생(회원)"
    )

    enrolled_at = models.DateTimeField("등록일", auto_now_add=True)
    is_active = models.BooleanField("수강중", default=True)

    class Meta:
        unique_together = ("program_class", "student")
        verbose_name = "프로그램 수강생"
        verbose_name_plural = "프로그램 수강생 목록"

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.program.name} ({self.program_class.name})"



# === 파일: courses/models.py ===
# 👉 프로그램 상품(ProgramProduct) & 기관 예약(InstitutionReservation) 모델 정의

from django.db import models
from django.contrib.auth.models import User
from teachers.models import TeachingInstitution

class Category(models.Model):
    """프로그램 카테고리 (추가/수정 가능)"""
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "카테고리"
        verbose_name_plural = "카테고리"

    def __str__(self):
        return self.name
    
class ProgramProduct(models.Model):
    """기관이 예약할 수 있는 프로그램 상품 (수강생 모집과 별개)"""
    STATUS_CHOICES = [
        ("public", "공개"),
        ("private", "비공개"),
    ]

    name = models.CharField("상품명", max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, default=1)
    duration_minutes = models.PositiveIntegerField("수업시간(분)", default=60)
    base_price = models.PositiveIntegerField("기본 가격(원)", default=0)
    description = models.TextField("설명", blank=True)
    
    # ✅ 재료비 관련
    include_material_cost = models.BooleanField("재료비 포함 여부", default=True)
    included_materials = models.TextField("포함 재료 설명", blank=True)
    
    # ✅ 새 필드
    topics = models.JSONField("주제", default=list, blank=True)   # 여러 개 저장 가능
    image = models.ImageField("프로그램 이미지", upload_to="products/", null=True, blank=True)
    status = models.CharField("공개 상태", max_length=20, choices=STATUS_CHOICES, default="private")  # ✅ 추가
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
    
class ProductMaterial(models.Model):
    product = models.ForeignKey(ProgramProduct, on_delete=models.CASCADE, related_name="materials")
    name = models.CharField("재료명", max_length=100)
    price = models.PositiveIntegerField("가격(원)", default=0)

    def __str__(self):
        return f"{self.name} ({self.price}원)"



class InstitutionReservation(models.Model):
    """기관이 특정 날짜/시간에 프로그램 상품을 예약"""
    STATUS_CHOICES = [
        ("requested", "예약요청"),
        ("approved", "예약확정"),
        ("canceled", "예약취소"),
    ]

    institution = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reservations_as_institution",
        verbose_name="기관 회원"
    )

    product = models.ForeignKey(
        ProgramProduct, on_delete=models.PROTECT, related_name="reservations", verbose_name="프로그램 상품"
    )
    requested_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="요청자"
    )

    date = models.DateField("수업 날짜")
    start_time = models.TimeField("시작 시간")
    end_time = models.TimeField("종료 시간")

    headcount = models.PositiveIntegerField("예상 인원", default=10)
    place = models.CharField("수업 장소", max_length=200, blank=True)
    memo = models.TextField("요청 메모", blank=True)

    # ✅ 주제 필드 추가
    selected_topic = models.CharField("선택 주제", max_length=200, blank=True)
    
    status = models.CharField("상태", max_length=20, choices=STATUS_CHOICES, default="requested")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "start_time"]

    def __str__(self):
        inst_name = (
            self.institution.institution_profile.institution_name
            if hasattr(self.institution, "institution_profile") else self.institution.username
        )
        return f"{self.date} {inst_name} - {self.product} ({self.selected_topic})"

