from django.db import models
from django.utils import timezone

class RobotLevelUp(models.Model):
    # ✅ 출강장소 연결
    institution = models.ForeignKey(
        "teachers.TeachingInstitution",
        on_delete=models.CASCADE,
        verbose_name="출강장소",
        related_name="levelups",
        null=True,
        blank=True
    )

    year_month = models.CharField("년월", max_length=7, help_text="예: 2025-11")  # YYYY-MM

    # 교구명 (외래키)
    material = models.ForeignKey(
        "materials.Material",
        on_delete=models.PROTECT,
        verbose_name="교구명",
        null=True,
        blank=True
    )

    section = models.CharField("부", max_length=20, blank=True)
    grade = models.PositiveIntegerField("학년", null=True, blank=True)
    class_no = models.PositiveIntegerField("반", null=True, blank=True)
    student_no = models.PositiveIntegerField("번호", null=True, blank=True)
    student_name = models.CharField("학생명", max_length=50)

    guide_done = models.BooleanField("안내완료", default=False)
    guide_date = models.DateField("안내일", null=True, blank=True)
    release_done = models.BooleanField("출고완료", default=False)
    release_date = models.DateField("출고일", null=True, blank=True)
    delivery_done = models.BooleanField("전달완료", default=False)
    delivery_date = models.DateField("전달일", null=True, blank=True)

    price = models.PositiveIntegerField("가격", default=0)
    note = models.CharField("비고", max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.institution}] {self.student_name} ({self.year_month})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "로봇 단계업"
        verbose_name_plural = "로봇 단계업 관리"

    def kit_name(self):
        return self.material.name if self.material else "-"
    kit_name.short_description = "교구명"
