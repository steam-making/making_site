# blog_auto/models.py
from django.db import models


class BlogCategory(models.TextChoices):
    AI_AICE = "ai_aice", "AI / AICE"
    ROBOT_CODING = "robot_coding", "로봇 코딩"
    CREATIVE_MATH = "creative_math", "창의수학"
    SCIENCE = "science", "과학탐구"
    TEACHER_TRAINING = "teacher_training", "강사 교육"


class AutoPost(models.Model):
    PLATFORM_NAVER = "naver"
    PLATFORM_TISTORY = "tistory"
    PLATFORM_BOTH = "both"
    PLATFORM_CHOICES = [
        (PLATFORM_NAVER, "네이버만"),
        (PLATFORM_TISTORY, "티스토리만"),
        (PLATFORM_BOTH, "두 곳 모두"),
    ]

    STATUS_DRAFT = "draft"
    STATUS_READY = "ready"          # 발행 준비 완료 (예약/수동 발행 대상)
    STATUS_SCHEDULED = "scheduled"  # 예약 발행 걸려 있음
    STATUS_PUBLISHED = "published"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "작성중"),
        (STATUS_READY, "발행 준비"),
        (STATUS_SCHEDULED, "예약"),
        (STATUS_PUBLISHED, "발행 완료"),
        (STATUS_FAILED, "실패"),
    ]

    topic = models.CharField("주제(내부용)", max_length=255)
    main_title = models.CharField("선택된 제목", max_length=255)
    alt_titles = models.JSONField("대체 제목들", default=list, blank=True)
    category = models.CharField(
        "카테고리",
        max_length=50,
        choices=BlogCategory.choices,
        default=BlogCategory.AI_AICE,
    )

    raw_response = models.JSONField("GPT 원본 응답(JSON)", blank=True, null=True)
    content = models.TextField("본문 내용")
    keywords = models.JSONField("키워드 리스트", default=list, blank=True)
    cta = models.CharField("CTA 문구", max_length=500, blank=True)

    thumbnail = models.ImageField(
        "썸네일 이미지",
        upload_to="blog_thumbnails/",
        blank=True,
        null=True,
    )

    platform = models.CharField(
        "발행 플랫폼",
        max_length=20,
        choices=PLATFORM_CHOICES,
        default=PLATFORM_BOTH,
    )

    status = models.CharField(
        "상태",
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
    )

    publish_at = models.DateTimeField("예약 발행 시간", blank=True, null=True)
    published_at = models.DateTimeField("실제 발행 시간", blank=True, null=True)

    naver_post_id = models.CharField("네이버 포스트 ID", max_length=100, blank=True)
    tistory_post_id = models.CharField("티스토리 포스트 ID", max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_status_display()}] {self.main_title}"
