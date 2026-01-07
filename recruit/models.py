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

    def __str__(self):
        return self.name

    @property
    def current_count(self):
        """
        현재 수강 인원 (신청 테이블 기준 계산)
        """
        return self.recruitapply_set.count()
