from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date
import calendar


class WorkType(models.Model):
    """업무 종류 (예: 개인, 학교, 학원 등)"""
    name = models.CharField("업무종류명", max_length=50, unique=True)
    order = models.PositiveIntegerField("표시순서", default=1)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "업무 종류"
        verbose_name_plural = "업무 종류 목록"

    def __str__(self):
        return self.name


class Task(models.Model):
    """할일 관리"""

    REPEAT_CHOICES = [
        ('none', '반복 없음'),
        ('daily', '매일'),
        ('weekly', '매주'),
        ('monthly', '매월'),
        ('yearly', '매년'),
    ]

    title = models.CharField("업무 제목", max_length=200)
    description = models.TextField("내용", blank=True)
    work_type = models.ForeignKey(
        WorkType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="업무 종류"
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="작성자")
    created_at = models.DateField("작성일자", default=timezone.now)
    due_date = models.DateField("마감일자", null=True, blank=True)
    completed = models.BooleanField("완료 여부", default=False)
    completed_at = models.DateTimeField("종료일자", null=True, blank=True)

    # ✅ 반복 주기 필드 추가
    repeat = models.CharField(
        "반복 주기",
        max_length=10,
        choices=REPEAT_CHOICES,
        default='none',
        help_text="업무가 반복되는 주기를 설정합니다.",
    )

    def __str__(self):
        return f"{self.title} ({self.work_type or '미지정'})"

    # ✅ 다음 반복 업무의 마감일 계산
    def get_next_due_date(self):
        """반복 주기에 따라 다음 마감일 계산"""
        if not self.due_date:
            return None

        if self.repeat == 'daily':
            return self.due_date + timedelta(days=1)
        elif self.repeat == 'weekly':
            return self.due_date + timedelta(weeks=1)
        elif self.repeat == 'monthly':
            year = self.due_date.year
            month = self.due_date.month + 1
            if month > 12:
                month = 1
                year += 1
            day = min(self.due_date.day, calendar.monthrange(year, month)[1])
            return date(year, month, day)
        elif self.repeat == 'yearly':
            year = self.due_date.year + 1
            month = self.due_date.month
            day = min(self.due_date.day, calendar.monthrange(year, month)[1])
            return date(year, month, day)
        return None

    # ✅ 완료 시 다음 반복 업무 자동 생성
    def create_next_task_if_repeated(self):
        """
        반복 주기가 설정된 업무가 완료되면
        다음 주기의 새 Task를 자동 생성합니다.
        """
        next_due = self.get_next_due_date()
        if next_due:
            Task.objects.create(
                title=self.title,
                description=self.description,
                work_type=self.work_type,
                created_by=self.created_by,
                due_date=next_due,
                repeat=self.repeat,
            )
