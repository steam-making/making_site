from django.db import models
from teachers.models import TeachingInstitution  # ✅ 기존 출강장소 모델 참조


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

    def __str__(self):
        return f"{self.name} ({self.grade} {self.class_name})"
