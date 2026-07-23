# teachers/models.py

from django.db import models
from django.contrib.auth.models import User
from datetime import date
from calendar import monthrange

from schools.models import School

class TeachingInstitution(models.Model):
    PLACE_TYPE_CHOICES = (
        ("school", "학교"),
        ("kindergarten", "유치원"),
        ("child_center", "지역아동센터"),
        ("culture_center", "문화센터"),
        ("other", "기타 기관"),
    )

    teacher = models.ForeignKey(User, on_delete=models.CASCADE)

    # 🔥 반드시 추가
    place_type = models.CharField(
        max_length=20,
        choices=PLACE_TYPE_CHOICES,
        default="school",
        verbose_name="출강 장소 유형"
    )

    # 🔥 새로 추가
    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teaching_institutions"
    )

    # 🔁 기존 필드 (유지)
    name = models.CharField(max_length=100)

    program = models.CharField(max_length=100)

    days = models.ManyToManyField('TeachingDay')

    created_at = models.DateTimeField(auto_now_add=True)

    contact_email = models.EmailField(blank=True, null=True)
    admin_email = models.EmailField(blank=True, null=True)
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.school.name if self.school else self.name} - {self.program}"


class TeachingDay(models.Model):
    code = models.CharField(max_length=2, unique=True)  # 예: '월'
    name = models.CharField(max_length=10)              # 예: '월요일'

    def __str__(self):
        return self.name

class Certificate(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="certificates")
    name = models.CharField("자격증명", max_length=200)
    issued_by = models.CharField("발급기관", max_length=200, blank=True)
    issued_date = models.DateField("발급일", null=True, blank=True)
    expires_date = models.DateField("만료일", null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.teacher.first_name}"


class CertificateCatalogItem(models.Model):
    """취득 대상 자격증 리스트(카탈로그). 관리자가 추가/수정/삭제 가능."""
    category = models.CharField("종류", max_length=50)
    auth_type = models.CharField("인증", max_length=50, help_text="예: 민간, 국가공인")
    name = models.CharField("자격증명", max_length=200)
    issuer = models.CharField("발행처", max_length=200, blank=True)

    course_intro = models.TextField("과정 소개", blank=True)
    educational_goal = models.TextField("교육 목표", blank=True)

    validity = models.CharField("유효기간", max_length=100, blank=True)
    issue_fee = models.CharField("발급비", max_length=100, blank=True)
    education_fee = models.CharField("교육비", max_length=100, blank=True)
    materials = models.CharField("교구재", max_length=200, blank=True)
    min_students = models.CharField("최소수강인원", max_length=100, blank=True)
    session_length = models.CharField("1차시 시간", max_length=50, blank=True)
    session_count = models.PositiveIntegerField("교육차시", null=True, blank=True)
    curriculum = models.TextField("차시별 커리큘럼", blank=True, help_text="한 줄에 한 차시씩 입력")

    exam_type = models.CharField("시험형태", max_length=200, blank=True)
    exam_fee = models.CharField("시험비", max_length=100, blank=True)

    related_link = models.URLField("관련링크", max_length=500, blank=True)
    related_recruit = models.ForeignKey(
        "recruit.InstructorRecruit",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="catalog_items",
        verbose_name="연결된 교육과정(모집공고)",
    )

    order = models.PositiveIntegerField("표시 순서", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name

    def curriculum_list(self):
        return [line.strip() for line in self.curriculum.splitlines() if line.strip()]


from django.db import models
from datetime import date

class Career(models.Model):
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="careers",
        verbose_name="강사",
        null=True, blank=True   # ✅ 기존 데이터 대비 안전
    )
    organization = models.CharField(
        max_length=200,
        verbose_name="기관명",
        default="기관명 미입력"   # ✅ 기본값 추가
    )
    position = models.CharField(
        max_length=100,
        verbose_name="직책",
        default="직책 미입력"     # ✅ 기본값 추가
    )
    start_date = models.DateField(
        verbose_name="시작일",
        default=date.today        # ✅ 오늘 날짜를 기본값으로
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="종료일"
    )
    description = models.TextField(
        blank=True,
        verbose_name="세부내용",
        default=""                # ✅ 빈 문자열 기본값
    )

    def __str__(self):
        return f"{self.organization} - {self.position}"

    def period_display(self):
        sd = self.start_date.strftime("%Y-%m-%d")
        ed = self.end_date.strftime("%Y-%m-%d") if self.end_date else "현재"
        return f"{sd} ~ {ed}"

    def duration_display(self):
        from calendar import monthrange
        end = self.end_date or date.today()
        y, m, d = self._ymd_between(self.start_date, end)

        parts = []
        if y: parts.append(f"{y}년")
        if m: parts.append(f"{m}개월")
        if d or not parts: parts.append(f"{d}일")
        return " ".join(parts)

    @staticmethod
    def _ymd_between(start, end):
        from calendar import monthrange
        y = end.year - start.year
        m = end.month - start.month
        d = end.day - start.day

        if d < 0:
            prev_month = end.month - 1 or 12
            prev_year = end.year - 1 if end.month == 1 else end.year
            d += monthrange(prev_year, prev_month)[1]
            m -= 1

        if m < 0:
            m += 12
            y -= 1

        return y, m, d

