from django.db import models

from django.db import models


class SourceSite(models.Model):

    AREA_CHOICES = (
        ("GWANGJU", "광주"),
        ("JEONNAM", "전남"),
    )

    area = models.CharField(
        "관리 지역",
        max_length=10,
        choices=AREA_CHOICES,
        default="GWANGJU",
        db_index=True,
        help_text="광주 / 전남 구분"
    )

    name = models.CharField("사이트명", max_length=100)
    url = models.URLField("목록 URL")
    active = models.BooleanField("사용 여부", default=True)

    REQUEST_METHOD_CHOICES = (
        ("GET", "GET"),
        ("POST", "POST"),
    )
    request_method = models.CharField(
        "요청 방식",
        max_length=10,
        choices=REQUEST_METHOD_CHOICES,
        default="GET",
    )

    extra_params = models.JSONField(
        "추가 파라미터",
        blank=True,
        null=True,
        help_text="POST 또는 GET으로 함께 전송할 파라미터 (dict 형태)"
    )

    list_selector = models.CharField(
        "목록 셀렉터",
        max_length=200,
        help_text="게시글 목록 CSS Selector"
    )
    title_selector = models.CharField("제목 셀렉터", max_length=200)
    link_selector = models.CharField("링크 셀렉터", max_length=200)
    date_selector = models.CharField("날짜 셀렉터", max_length=200, blank=True)

    collector = models.CharField(
        max_length=30,
        choices=(
            ("NEULBOM", "늘봄허브"),
            ("JNE_COMMON", "전남교육청 공통"),
            ("JNE_REGION", "전남교육청 지역형"),
        )
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_area_display()}] {self.name}"


import re
from datetime import date, timedelta

from django.db import models


class CollectedPost(models.Model):
    source = models.ForeignKey(
        SourceSite,
        on_delete=models.CASCADE,
        related_name="posts"
    )

    title = models.CharField(max_length=300)

    # 🔥 늘봄허브 핵심 ID (파일 다운로드에도 사용)
    mng_no = models.CharField(
        "공고 관리번호",
        max_length=50,
        blank=True,
        db_index=True
    )

    link = models.URLField()

    region = models.CharField("지역", max_length=100, blank=True)
    school_name = models.CharField("학교명", max_length=150, blank=True)

    # 🔹 모집 기간 문자열
    # 예: 2025.03.01 ~ 2025.03.10
    post_date = models.CharField(max_length=50, blank=True)

    status = models.CharField(
        "상태",
        max_length=30,
        blank=True,
        help_text="모집중 / 마감 등 (자동 계산)"
    )

    # ✅ NEW 여부 (수집 시점 기준)
    is_new = models.BooleanField(default=True)

    collected_at = models.DateTimeField(auto_now_add=True)

    # ==================================================
    # ✅ 추가된 필드 (상세 페이지 수집용)
    # ==================================================

    weekday = models.CharField(
        "운영요일",
        max_length=50,
        blank=True,
        help_text="예: 월, 수, 금"
    )

    attachment_urls = models.JSONField(
        "첨부파일 URL 목록",
        default=list,
        blank=True,
        help_text='[{"name": "...", "url": "..."}]'
    )

    class Meta:
        unique_together = ("source", "mng_no")
        ordering = ["-collected_at"]

    def __str__(self):
        return self.title

    # ==================================================
    # 🔥 모집 상태 자동 계산 (post_date 기반)
    # ==================================================
    def get_auto_status(self):
        """
        post_date 예시:
        - 2025.03.01 ~ 2025.03.10
        - 2025-03-01~2025-03-10
        - 03.01 ~ 03.10
        """

        if not self.post_date:
            return ""

        # 날짜 형태 추출
        dates = re.findall(r"\d{2,4}[./\-]\d{1,2}[./\-]\d{1,2}", self.post_date)
        if len(dates) < 2:
            return ""

        def parse_date(d):
            d = re.sub(r"[./]", "-", d)
            parts = d.split("-")

            # 연도 없는 경우 → 올해 기준
            if len(parts[0]) == 2:
                year = date.today().year
                month, day = map(int, parts)
            else:
                year, month, day = map(int, parts)

            return date(year, month, day)

        try:
            start_date = parse_date(dates[0])
            end_date = parse_date(dates[1])
        except Exception:
            return ""

        today = date.today()

        if today < start_date:
            return "예정"
        elif today > end_date:
            return "마감"
        elif end_date - today <= timedelta(days=3):
            return "마감임박"
        else:
            return "모집중"


class NeulbomConfig(models.Model):
    cutoff_date = models.DateField(verbose_name="늘봄 수집 기준 날짜")

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"늘봄 기준일: {self.cutoff_date}"


class LinkhubConfig(models.Model):
    """linkhub 자동수집/자동삭제 설정"""
    auto_collect = models.BooleanField("자동수집 ON/OFF", default=False)
    expire_deadline_days = models.PositiveIntegerField("마감 후 삭제 기준(일)", default=3)
    expire_no_deadline_days = models.PositiveIntegerField("등록일 기준 삭제(일, 마감일 없는 공고)", default=30)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "linkhub 설정"

    def __str__(self):
        return f"LinkhubConfig (자동수집={self.auto_collect})"

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj