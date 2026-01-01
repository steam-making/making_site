import random
from collections import Counter
from .models import LottoResult
import pandas as pd
from django.conf import settings
import os

EXCEL_PATH = os.path.join(settings.BASE_DIR, "lotto_results.xlsx")

def load_lotto_data():
    if not os.path.exists(EXCEL_PATH):
        return pd.DataFrame()
    df = pd.read_excel(EXCEL_PATH)
    return df

def get_recent_numbers(n=10):
    """최근 n회차 당첨번호 불러오기"""
    results = LottoResult.objects.order_by("-draw_no")[:n]
    nums = []
    for r in results:
        nums.extend(r.get_numbers())
    return nums

def generate_recommendations(n_recent=10, n_sets=10):
    numbers = get_recent_numbers(n_recent)
    counter = Counter(numbers)

    sorted_nums = [num for num, cnt in counter.most_common()]

    core = sorted(sorted_nums[:10])  # ✅ 오름차순 정렬
    all_nums = set(range(1, 46))
    remaining = list(all_nums - set(core))
    random.shuffle(remaining)
    support = sorted(remaining[:10])  # ✅ 오름차순 정렬

    recommendations = []
    for _ in range(n_sets):
        core_pick = random.sample(core, min(len(core), 4))
        support_pick = random.sample(support, min(len(support), 2))
        combo = sorted(set(core_pick + support_pick))
        recommendations.append(combo)

    return core, support, recommendations
