from django.db import models
from django.contrib.auth.models import User


class TypingStage(models.Model):
    """
    타자 연습 단계 정의
    """

    STAGE_TYPE_CHOICES = [
        ("POSITION", "자리연습"),
        ("WORD", "낱말연습"),
        ("SENTENCE", "단문연습"),
        ("PARAGRAPH", "장문연습"),
    ]

    LANG_CHOICES = [
        ("KO", "한글"),
        ("EN", "영어"),
    ]

    name = models.CharField("단계명", max_length=50)
    stage_type = models.CharField("연습 유형", max_length=20, choices=STAGE_TYPE_CHOICES)

    # ✅ 통과 기준
    min_speed = models.IntegerField("최소 타수", default=0)
    min_accuracy = models.IntegerField("최소 정확도(%)", default=0)
    max_typo = models.IntegerField("허용 오타 수", default=999)

    order = models.PositiveIntegerField("단계 순서", default=0)

    # ✅ 1번(자리연습) 구현용 필드
    language = models.CharField("언어", max_length=2, choices=LANG_CHOICES, default="KO")
    duration_seconds = models.PositiveIntegerField("연습 시간(초)", default=60)
    practice_chars = models.TextField(
        "연습 문자(쉼표로 구분)",
        blank=True,
        help_text="예: ㅁ,ㄴ,ㅇ,ㄹ 또는 a,s,d,f",
    )

    def __str__(self):
        return f"{self.get_stage_type_display()} - {self.name} ({self.get_language_display()})"


class TypingResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stage = models.ForeignKey(TypingStage, on_delete=models.CASCADE)

    speed = models.IntegerField("타수(타/분)")
    accuracy = models.FloatField("정확도")
    typo_count = models.IntegerField("오타 수")
    duration = models.IntegerField("진행 시간(초)")

    passed = models.BooleanField("통과 여부", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.stage} ({self.speed}타)"
