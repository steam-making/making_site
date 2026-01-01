from django.core.management.base import BaseCommand
from typing_trainer.models import TypingStage


class Command(BaseCommand):
    help = "타자연습 기본 Stage(자리연습) 생성"

    def handle(self, *args, **options):
        # ✅ 기본자리(한글) - 예: ㅁ ㄴ ㅇ ㄹ (홈 포지션 연습용 예시)
        TypingStage.objects.update_or_create(
            stage_type="POSITION",
            name="기본자리",
            language="KO",
            defaults=dict(
                order=1,
                duration_seconds=60,
                practice_chars="ㅁ,ㄴ,ㅇ,ㄹ,ㅏ,ㅣ",  # 필요 시 확장
                min_speed=150,
                min_accuracy=95,
                max_typo=1,
            ),
        )

        # ✅ 기본자리(영어) - ASDF JKL; 느낌
        TypingStage.objects.update_or_create(
            stage_type="POSITION",
            name="기본자리",
            language="EN",
            defaults=dict(
                order=2,
                duration_seconds=60,
                practice_chars="a,s,d,f,j,k,l,;",
                min_speed=150,
                min_accuracy=95,
                max_typo=1,
            ),
        )

        self.stdout.write(self.style.SUCCESS("✅ 기본 Stage 생성 완료"))
