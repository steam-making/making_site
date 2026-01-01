from django.db import models
from django.contrib.auth.models import User

class Notice(models.Model):
    AUDIENCE_CHOICES = [
        ("all", "전체"),
        ("parent", "학부모"),
        ("student", "학생"),
        ("teacher", "강사"),
    ]
    STATUS_CHOICES = [
        ("draft", "임시저장"),
        ("published", "게시"),
    ]

    title = models.CharField("제목", max_length=200)
    content = models.TextField("내용")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="작성자")
    audience = models.CharField("대상", max_length=10, choices=AUDIENCE_CHOICES, default="all", db_index=True)
    status = models.CharField("상태", max_length=10, choices=STATUS_CHOICES, default="published", db_index=True)
    is_pinned = models.BooleanField("상단 고정", default=False, db_index=True)
    attachment = models.FileField("첨부파일", upload_to="notices/%Y/%m/", blank=True, null=True)
    view_count = models.PositiveIntegerField("조회수", default=0)
    published_at = models.DateTimeField("게시일", auto_now_add=True)

    class Meta:
        ordering = ["-is_pinned", "-published_at"]

    def __str__(self):
        return self.title
