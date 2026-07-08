from django.conf import settings
from django.db import models
from teachers.models import TeachingInstitution  # ✅ 기존 출강장소 모델 참조


class MedutechAccount(models.Model):
    """medutech.kr(making_attendance)에서 발급받은 개인 API 토큰"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='medutech_account')
    api_token = models.CharField("API 토큰", max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - medutech 연동"


class MedutechSchoolMapping(models.Model):
    """출강장소(TeachingInstitution)와 medutech.kr 학교를 1:1로 매핑"""
    institution = models.OneToOneField(TeachingInstitution, on_delete=models.CASCADE, related_name='medutech_mapping')
    medutech_school_id = models.IntegerField("medutech 학교 ID")
    medutech_school_name = models.CharField("medutech 학교명", max_length=100, blank=True)
    medutech_program_name = models.CharField("medutech 프로그램명", max_length=100, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.institution} -> medutech#{self.medutech_school_id}"


class ProgramDivision(models.Model):
    DIVISION_CHOICES = [
        ('1부', '1부'),
        ('2부', '2부'),
        ('3부', '3부'),
    ]
    institution = models.ForeignKey(TeachingInstitution, on_delete=models.CASCADE, related_name='divisions')
    division = models.CharField("부서", choices=DIVISION_CHOICES, max_length=10)
    capacity = models.PositiveIntegerField("정원", default=0)

    def __str__(self):
        # ✅ 출강장소명 제외하고 부서명만 반환
        return self.division

class Student(models.Model):
    division = models.ForeignKey(ProgramDivision, on_delete=models.CASCADE, related_name='students')
    grade = models.CharField("학년", max_length=10)
    class_name = models.CharField("반", max_length=10)
    number = models.CharField("번호", max_length=10)
    name = models.CharField("학생 이름", max_length=50)
    parent_contact = models.CharField("학부모 연락처", max_length=20)
    medutech_student_id = models.IntegerField("medutech 학생 ID", null=True, blank=True, db_index=True)

    def __str__(self):
        return f"{self.name} ({self.grade} {self.class_name})"
