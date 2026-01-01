from django.db import models

class School(models.Model):
    name = models.CharField(max_length=100)
    school_code = models.CharField(max_length=20, blank=True, null=True)  # NEIS 학교코드
    student_count = models.CharField(max_length=50, null=True, blank=True)
    homepage = models.CharField(max_length=200, blank=True, null=True)
    zipcode = models.CharField(max_length=10, blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    office_phone = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name
