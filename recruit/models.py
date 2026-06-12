from django.db import models
from django.db.models import JSONField
from schools.models import School

class RecruitNotice(models.Model):
    status = models.CharField(max_length=20, default="예정")  # 자동 계산용

    receive_date = models.DateField()
    deadline = models.DateTimeField()

    # 다중 선택이므로 CharField로 콤마 저장
    submit_method = models.CharField(max_length=200)

    region = models.CharField(max_length=50)
    school = models.ForeignKey(
        "schools.School",
        on_delete=models.SET_NULL,
        null=True
    )
    student_count = models.CharField(max_length=20, blank=True)

    programs = JSONField(blank=True, null=True)
    attachment_urls = JSONField(blank=True, null=True)

    # ⭐ 추가
    is_our_school = models.BooleanField(
        default=False,
        verbose_name="우리 강사 출강 학교",
        null=True
    )

from django.db import models

DAYS_OF_WEEK = [
    (1, "월"),
    (2, "화"),
    (3, "수"),
    (4, "목"),
    (5, "금"),
    (6, "토"),
]

class RecruitProgram(models.Model):
    name = models.CharField("프로그램명", max_length=100)
    day = models.IntegerField("요일", choices=DAYS_OF_WEEK)
    start_time = models.TimeField("시작 시간")
    end_time = models.TimeField("종료 시간")
    capacity = models.PositiveIntegerField("정원")

    # ✅ 과목 고정 색상
    color_class = models.CharField(
        "시간표 색상",
        max_length=30,
        default="timetable-blue",
        help_text="CSS 클래스명 (예: timetable-blue)"
    )

    def __str__(self):
        return self.name

    @property
    def current_count(self):
        """
        현재 수강 인원 (신청 테이블 기준 계산)
        """
        return self.recruitapply_set.count()


class InstructorCourseType(models.Model):
    CERT_TYPE_CHOICES = [
        ("national", "국가자격"),
        ("authorized", "국가공인"),
        ("private", "민간자격"),
        ("none", "해당없음/수료증"),
    ]

    name = models.CharField("과정명", max_length=100)
    course_intro = models.TextField("과정 소개", blank=True)
    educational_goal = models.TextField("교육 목표", blank=True)
    curriculum = models.JSONField("커리큘럼", default=list, blank=True)
    
    certificate_agency = models.CharField("발급기관", max_length=100, blank=True)
    certificate_type = models.CharField("자격증 종류", max_length=20, choices=CERT_TYPE_CHOICES, blank=True)

    cost_education = models.PositiveIntegerField("교육비", default=0)
    cost_certificate = models.PositiveIntegerField("자격발급비", default=0)
    cost_material = models.PositiveIntegerField("교재/교구비", default=0)
    cost_includes_all = models.BooleanField("비용 일체 포함 여부", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "지도사과정 유형"
        verbose_name_plural = "지도사과정 유형 목록"
        ordering = ["name"]

    def __str__(self):
        return self.name


class InstructorRecruit(models.Model):
    STATUS_CHOICES = [
        ("open", "모집중"),
        ("closed", "마감"),
        ("hidden", "비공개"),
    ]
    
    CERT_TYPE_CHOICES = [
        ("national", "국가자격"),
        ("authorized", "국가공인"),
        ("private", "민간자격"),
        ("none", "해당없음/수료증"),
    ]

    course_type = models.ForeignKey(
        InstructorCourseType, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        verbose_name="과정 종류"
    )
    title = models.CharField("공고명", max_length=200)
    course_intro = models.TextField("과정 소개", blank=True)
    educational_goal = models.TextField("교육 목표", blank=True)
    curriculum = models.JSONField("커리큘럼", default=list, blank=True)
    
    certificate_agency = models.CharField("발급기관", max_length=100, blank=True)
    certificate_type = models.CharField("자격증 종류", max_length=20, choices=CERT_TYPE_CHOICES, blank=True)

    cost_education = models.PositiveIntegerField("교육비", default=0)
    cost_certificate = models.PositiveIntegerField("자격발급비", default=0)
    cost_material = models.PositiveIntegerField("교재/교구비", default=0)
    cost_includes_all = models.BooleanField("비용 일체 포함 여부", default=False)
    
    recruit_start = models.DateTimeField("모집 시작일")
    recruit_end = models.DateTimeField("모집 마감일")
    capacity = models.PositiveIntegerField("모집 정원", default=0, help_text="0이면 제한 없음")
    status = models.CharField("상태", max_length=20, choices=STATUS_CHOICES, default="hidden")
    image = models.ImageField("대표 이미지", upload_to="instructor_recruits/", blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "지도사과정 모집 공고"
        verbose_name_plural = "지도사과정 모집 공고"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class InstructorApplication(models.Model):
    STATUS_CHOICES = [
        ("pending", "신청완료"),
        ("approved", "승인"),
        ("rejected", "반려"),
        ("cancelled", "취소"),
    ]

    recruit = models.ForeignKey(InstructorRecruit, on_delete=models.CASCADE, related_name="applications", verbose_name="공고")
    
    applicant = models.ForeignKey(
        "accounts.Profile", 
        on_delete=models.CASCADE, 
        related_name="instructor_applications", 
        null=True, blank=True, 
        verbose_name="지원자(회원)"
    )
    
    applicant_name = models.CharField("이름", max_length=100)
    phone = models.CharField("연락처", max_length=30)
    memo = models.TextField("지원동기 및 남길말", blank=True)
    
    status = models.CharField("상태", max_length=20, choices=STATUS_CHOICES, default="pending")
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "지도사과정 지원 내역"
        verbose_name_plural = "지도사과정 지원 내역"
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.applicant_name} - {self.recruit.title}"
