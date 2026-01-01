from django.core.management.base import BaseCommand
from lotto_predictor.crawler import fetch_latest_lotto_results

class Command(BaseCommand):
    help = "Fetch and update latest Lotto results"

    def handle(self, *args, **kwargs):
        updated = fetch_latest_lotto_results()
        if updated:
            self.stdout.write(self.style.SUCCESS(f"{len(updated)}회차 업데이트 완료"))
        else:
            self.stdout.write("새로운 회차가 없습니다.")
