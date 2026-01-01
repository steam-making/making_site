from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import LottoResult, RecommendedSet
from .crawler import update_lotto_results

import pandas as pd, numpy as np, random
from lotto_predictor.services.recommender import (
    generate_ml_rule_sets,
    compute_probs,
    generate_many,
    rerank_and_pick,
    RerankConfig,
    generate_recent60_boosted_sets,
)


# ──────────────────────────────
# 번호 DataFrame 생성
# ──────────────────────────────
def get_all_numbers_df():
    qs = LottoResult.objects.all().values("draw_no", "numbers", "bonus")
    df = pd.DataFrame(qs)
    if df.empty:
        return df
    df[["num1","num2","num3","num4","num5","num6"]] = df["numbers"].str.split(",", expand=True).astype(int)
    return df

# ──────────────────────────────
# 추천 페이지
# ──────────────────────────────
def lotto_recommend(request):
    update_lotto_results()
    latest_result = LottoResult.objects.latest("draw_no")
    next_no = latest_result.draw_no + 1

    all_strategies = {
        "recent60": "⑥ Recent60 부스팅",
    }

    strategy_desc = {
        "recent60": "최근 60회 빈도 + 미세 미출 부스팅(0.3) + Shape 밸런스로 빠른 수렴",
    }

    strategies_list = [{"key": k, "name": v, "desc": strategy_desc[k]} for k, v in all_strategies.items()]
    selected = request.GET.getlist("strategies") or list(all_strategies.keys())

    recommendations = []
    if request.GET.getlist("strategies"):
        if "recent60" in selected:
            # 10세트 권장 (원하면 5로 바꿔도 됨)
            sets = generate_recent60_boosted_sets(n_sets=10)
            recommendations.append({
                "key": "recent60",
                "name": all_strategies["recent60"],
                "desc": strategy_desc["recent60"],
                "sets": sets
            })
    return render(request, "lotto_predictor/recommend.html", {
        "latest_result": latest_result,
        "next_no": next_no,
        "strategies": strategies_list,
        "selected_strategies": selected,
        "recommendations": recommendations,
    })

# ──────────────────────────────
# 저장 / 삭제
# ──────────────────────────────
@require_POST
def save_recommendations(request):
    next_no = int(request.POST.get("next_no"))
    sets = request.POST.getlist("sets")
    strategies = request.POST.getlist("strategies")
    for nums, strat in zip(sets, strategies):
        RecommendedSet.objects.create(draw_no=next_no, numbers=nums, strategy=strat)
    return redirect("lotto_saved")

@require_POST
def delete_recommendation(request, pk):
    rec = get_object_or_404(RecommendedSet, pk=pk)
    rec.delete()
    return redirect("lotto_saved")

@require_POST
def delete_recommendations_by_draw(request, draw_no):
    RecommendedSet.objects.filter(draw_no=draw_no).delete()
    return redirect("lotto_saved")

# ──────────────────────────────
# 저장된 추천 목록
# ──────────────────────────────
def lotto_saved(request):
    update_lotto_results()
    try:
        latest_result = LottoResult.objects.latest("draw_no")
    except LottoResult.DoesNotExist:
        latest_result = None

    grouped = {}
    for rec in RecommendedSet.objects.all().order_by("-draw_no", "-created_at"):
        rec_nums = set(rec.get_numbers())
        rec.match = None
        rec.match_numbers = []
        rec.bonus_hit = False
        rec.is_pending = True
        if latest_result and rec.draw_no <= latest_result.draw_no:
            try:
                result = LottoResult.objects.get(draw_no=rec.draw_no)
                winning = set(result.get_numbers())
                rec.match = len(rec_nums & winning)
                rec.match_numbers = rec_nums & winning
                rec.bonus_hit = result.bonus in rec_nums
                rec.is_pending = False
            except LottoResult.DoesNotExist:
                rec.is_pending = True
        grouped.setdefault(rec.draw_no, []).append(rec)

    grouped = dict(sorted(grouped.items(), key=lambda x: x[0], reverse=True))
    return render(request, "lotto_predictor/saved.html", {"grouped": grouped, "latest_result": latest_result})

# ──────────────────────────────
# ML+상관+반전 강화 백테스트 (회차 선택형)
# URL: /lotto/backtest/advanced/?draw_no=1194
# ──────────────────────────────
from django.utils.safestring import mark_safe
from lotto_predictor.services.recommender import (
    compute_probs,
    build_cooccurrence,
    normalize_cooccurrence,
    passes_rules,
    RuleConfig,
    advanced_score,
)
import io, base64
import pandas as pd, numpy as np
from django.views.decorators.cache import never_cache

from lotto_predictor.services.recommender import (
    compute_probs, build_cooccurrence, normalize_cooccurrence,
    passes_rules, RuleConfig, advanced_score
)

@never_cache
def lotto_backtest_recent60(request):
    """
    선택한 회차를 '모른다'고 가정하고 (draw_no-1까지로 학습),
    Recent60 부스팅 전략으로 추천 10세트를 생성한 뒤
    실제 당첨번호와의 적중 개수를 보여준다.
    """
    # 0) 시드 처리
    seed_param = request.GET.get("seed")
    try:
        seed = int(seed_param) if seed_param not in (None, "") else None
    except ValueError:
        seed = None

    # 1) 회차 확인
    all_qs = LottoResult.objects.all().order_by("draw_no")
    if not all_qs.exists():
        return render(request, "lotto_predictor/backtest_advanced.html", {
            "error": "DB에 당첨 결과가 없습니다."
        })

    max_draw = all_qs.last().draw_no
    selected_draw = int(request.GET.get("draw_no", max_draw))

    if selected_draw <= 1 or selected_draw > max_draw:
        return render(request, "lotto_predictor/backtest_advanced.html", {
            "error": f"유효한 회차를 입력하세요. (2 ~ {max_draw})",
            "max_draw": max_draw,
            "selected_draw": selected_draw,
            "seed": seed_param or "",
        })

    # 2) 학습 데이터 구성
    train_qs = LottoResult.objects.filter(draw_no__lt=selected_draw).order_by("draw_no")
    target = LottoResult.objects.get(draw_no=selected_draw)
    actual = target.get_numbers()
    actual_set = set(actual)

    # Pandas로 history 구성
    df = pd.DataFrame(list(train_qs.values("draw_no", "numbers")))
    df[["num1","num2","num3","num4","num5","num6"]] = df["numbers"].str.split(",", expand=True).astype(int)
    history = [list(df.loc[i, ["num1","num2","num3","num4","num5","num6"]]) for i in df.index]

    # 3) Recent60 부스팅으로 추천 세트 생성
    # 실행마다 시드 랜덤 부여 (새 번호 나오게)
    if seed is None:
        seed = np.random.randint(1, 999999)

    # seed값 고정해 reproducibility도 가능 (URL에 ?seed=123 입력 시 동일 조합)
    np.random.seed(seed)
    recommendations = generate_recent60_boosted_sets(n_sets=10)


    # 4) 적중 결과 계산
    results = []
    for idx, cand in enumerate(recommendations, 1):
        cand_set = set(cand)
        hit_nums = sorted(list(cand_set & actual_set))
        hit_cnt  = len(hit_nums)
        results.append({
            "rank": idx,
            "numbers": cand,
            "hit_cnt": hit_cnt,
            "hit_nums": hit_nums,
        })


    # 6) 렌더링 (기존 템플릿 재사용)
    return render(request, "lotto_predictor/backtest_advanced.html", {
        "max_draw": max_draw,
        "selected_draw": selected_draw,
        "actual": actual,
        "results": results,
        "seed": seed_param or "",
        "strategy_name": "Recent60 부스팅",  # 템플릿에서 표시용
    })

