from django.db import models

class LottoResult(models.Model):
    draw_no = models.IntegerField(unique=True)  # 회차
    numbers = models.CharField(max_length=50)   # "7,9,19,23,26,45"
    bonus = models.IntegerField()

    def get_numbers(self):
        return [int(n) for n in self.numbers.split(",")]

    def __str__(self):
        return f"{self.draw_no}회차"


class RecommendedSet(models.Model):
    draw_no = models.IntegerField()  # 추첨 예정 회차
    numbers = models.CharField(max_length=100)  # "1,5,13,22,29,37"
    strategy = models.CharField(max_length=20, default="freq")  # 전략 이름 저장
    created_at = models.DateTimeField(auto_now_add=True)

    def get_numbers(self):
        return [int(n) for n in self.numbers.split(",")]

    def match_count(self, lotto_result: LottoResult):
        if not lotto_result:
            return None
        return len(set(self.get_numbers()) & set(lotto_result.get_numbers()))

    def __str__(self):
        return f"{self.draw_no}회차 [{self.strategy}] ({self.numbers})"
