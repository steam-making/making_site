# progress/models.py

from datetime import timezone
from django.db import models
from accounts.models import User  # 학생/강사
from courses.models import Program  # 기존 프로그램 모델 가정

class ProgramLesson(models.Model):
    """프로그램 차시 정보"""
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="lessons")
    order = models.PositiveIntegerField(help_text="차시 번호")
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("program", "order")

    def __str__(self):
        return f"{self.program.name} - {self.order}차시"


class LessonProgress(models.Model):
    """학생 진도 체크"""
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"user_type": "student"},
        related_name="lesson_progress",
    )
    lesson = models.ForeignKey(
        ProgramLesson,
        on_delete=models.CASCADE,
        related_name="progress_records",
    )
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("student", "lesson")

    def complete(self):
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()

    def uncomplete(self):
        self.is_completed = False
        self.completed_at = None
        self.save()

    def __str__(self):
        return f"{self.student.username} - {self.lesson} ({self.is_completed})"
