# lotto_predictor/services/recommender.py
from dataclasses import dataclass
from typing import List, Dict, Tuple
from collections import Counter, defaultdict
import numpy as np
import random

from lotto_predictor.models import LottoResult

# ──────────────────────────────
# 규칙 설정 (완화 버전)
# ──────────────────────────────
@dataclass
class RuleConfig:
    odd_even: Tuple[int, int] = (2, 4)                    # 홀짝 2~4
    low_high: Tuple[int, int] = (2, 4)                    # 저/고 2~4
    allow_consecutive_pairs: Tuple[int, int] = (0, 2)     # 연속쌍 최대 2
    include_prev_count: Tuple[int, int] = (0, 3)          # 이월 최대 3
    sum_range: Tuple[int, int] = (80, 220)                # 합계 범위
    section_bins: Tuple[Tuple[int,int], ...] = ((1,10),(11,20),(21,30),(31,40),(41,45))
    section_distinct_range: Tuple[int,int] = (2, 5)       # 구간 다양성
    candidate_pool_size: int = 30
    max_tries: int = 10000

# 재랭킹 파이프라인 설정
@dataclass
class RerankConfig:
    candidate_pool_size: int = 32
    generate_count: int = 400
    pick_top: int = 10
    diversity_penalty: float = 0.25

# ──────────────────────────────
# 유틸
# ──────────────────────────────
def _consecutive_pairs(nums: List[int]) -> int:
    s = set(nums)
    return sum(1 for x in s if (x + 1) in s)

def _odd_even(nums: List[int]) -> Tuple[int,int]:
    odd = sum(1 for x in nums if x % 2)
    return odd, 6 - odd

def _low_high(nums: List[int]) -> Tuple[int,int]:
    low = sum(1 for x in nums if x <= 22)
    return low, 6 - low

def _section_count(nums: List[int], bins: Tuple[Tuple[int,int],...]) -> int:
    return sum(any(a <= n <= b for n in nums) for a, b in bins)

def _include_prev(nums: List[int], prev_nums: List[int]) -> int:
    return len(set(nums) & set(prev_nums)) if prev_nums else 0

# ──────────────────────────────
# 확률 추정 (지수감쇠 + 스무딩 + 미출현 캡)
# ──────────────────────────────
def compute_probs(history: List[List[int]], half_life: int = 60, smooth: float = 0.5, miss_cap: int = 20) -> Dict[int, float]:
    N = 45
    if not history:
        return {i: 6/45 for i in range(1, N+1)}

    T = len(history)
    lam = np.log(2) / max(1, half_life)
    weights = np.exp(lam * np.arange(T))
    weights = weights / weights.sum()

    # 가중 빈도
    wfreq = {i: 0.0 for i in range(1, N+1)}
    for t, nums in enumerate(history):
        for n in nums:
            wfreq[n] += weights[t]

    # 미출현 길이(캡)
    miss = {i: 0 for i in range(1, N+1)}
    for i in range(1, N+1):
        c = 0
        for row in reversed(history):
            if i in row:
                break
            c += 1
        miss[i] = min(c, miss_cap)

    raw = {}
    for i in range(1, N+1):
        base = wfreq[i] + smooth
        bonus = 0.03 * miss[i]
        raw[i] = base + bonus

    arr = np.array([raw[i] for i in range(1, N+1)], dtype=float)
    arr = np.clip(arr, 1e-7, None)
    arr = arr / arr.sum() * 6.0                      # 전체 기대합 ≈ 6
    return {i: float(arr[i-1]) for i in range(1, N+1)}

# ──────────────────────────────
# 룰 통과 검사
# ──────────────────────────────
def passes_rules(nums: List[int], prev_nums: List[int], cfg: RuleConfig) -> bool:
    odd, _   = _odd_even(nums)
    low, _   = _low_high(nums)
    cp       = _consecutive_pairs(nums)
    sec      = _section_count(nums, cfg.section_bins)
    inc      = _include_prev(nums, prev_nums)
    total    = sum(nums)
    return (
        cfg.odd_even[0] <= odd <= cfg.odd_even[1]
        and cfg.low_high[0] <= low <= cfg.low_high[1]
        and cfg.allow_consecutive_pairs[0] <= cp <= cfg.allow_consecutive_pairs[1]
        and cfg.section_distinct_range[0] <= sec <= cfg.section_distinct_range[1]
        and cfg.include_prev_count[0] <= inc <= cfg.include_prev_count[1]
        and cfg.sum_range[0] <= total <= cfg.sum_range[1]
    )

# ──────────────────────────────
# 기본형: 확률 + 룰 필터
# ──────────────────────────────
def generate_recommendations(draw_qs, how_many: int = 10, cfg: RuleConfig = RuleConfig()) -> List[List[int]]:
    history = [obj.get_numbers() for obj in draw_qs.order_by('-draw_no')][::-1]
    prev = history[-1] if history else []
    probs = compute_probs(history)
    pool = [n for n, _ in sorted(probs.items(), key=lambda x: x[1], reverse=True)[:cfg.candidate_pool_size]]

    results = []
    tries = 0
    while len(results) < how_many and tries < cfg.max_tries:
        tries += 1
        w = np.array([probs[p] for p in pool], dtype=float); w = np.clip(w, 1e-9, None); w /= w.sum()
        cand = sorted(list(np.random.choice(pool, 6, replace=False, p=w)))
        if passes_rules(cand, prev, cfg):
            t = tuple(cand)
            if t not in results:
                results.append(cand)
    return results

# ──────────────────────────────
# 개선형 파이프라인: 대량 생성 → 재랭킹
# ──────────────────────────────
def generate_many(history: List[List[int]], probs: Dict[int, float], rerank: RerankConfig) -> List[List[int]]:
    prev = history[-1] if history else []
    pool = [n for n, _ in sorted(probs.items(), key=lambda x: x[1], reverse=True)[:rerank.candidate_pool_size]]
    bag, tries = [], 0
    rng = np.random.default_rng(42)
    while len(bag) < rerank.generate_count and tries < rerank.generate_count * 30:
        tries += 1
        w = np.array([probs[p] for p in pool], dtype=float); w = np.clip(w, 1e-9, None); w /= w.sum()
        cand = sorted(list(rng.choice(pool, size=6, replace=False, p=w)))
        if passes_rules(cand, prev, RuleConfig()):
            bag.append(cand)
    # 중복 제거
    uniq, seen = [], set()
    for c in bag:
        t = tuple(c)
        if t not in seen:
            uniq.append(c); seen.add(t)
    return uniq

def _prob_score(nums: List[int], probs: Dict[int, float]) -> float:
    return float(sum(probs[n] for n in nums))

def _band_bonus(nums: List[int]) -> float:
    # 합 150 중심 선호 (±80 폭)
    return 1.0 - abs(sum(nums) - 150) / 80.0

def rerank_and_pick(cands: List[List[int]], probs: Dict[int, float], rerank: RerankConfig) -> List[List[int]]:
    def base_score(nums: List[int]) -> float:
        return _prob_score(nums, probs) + 0.15 * _band_bonus(nums)

    picked: List[Tuple[float, List[int]]] = []
    for c in sorted(cands, key=lambda x: -base_score(x)):
        penalty = 0.0
        for _, p in picked:
            overlap = len(set(c) & set(p))
            penalty += rerank.diversity_penalty * max(0, overlap - 2)
        picked.append((base_score(c) - penalty, c))
        if len(picked) >= rerank.pick_top:
            break
    return [c for _, c in sorted(picked, key=lambda x: -x[0])]

# 외부 호출(개선형)
def generate_ml_rule_sets(n_sets: int = 10) -> List[List[int]]:
    qs = LottoResult.objects.order_by('-draw_no')[:1000]
    history = [r.get_numbers() for r in qs][::-1]
    probs = compute_probs(history)
    rerank = RerankConfig(candidate_pool_size=32, generate_count=max(200, n_sets * 40), pick_top=n_sets, diversity_penalty=0.25)
    many = generate_many(history, probs, rerank)
    return rerank_and_pick(many, probs, rerank)

# ──────────────────────────────
# 고급형: ML + 상관관계 + 반전번호 강화
# ──────────────────────────────
def build_cooccurrence(history: List[List[int]]) -> Dict[int, Dict[int, int]]:
    co = defaultdict(lambda: defaultdict(int))
    for nums in history:
        s = set(nums)
        for a in s:
            for b in s:
                if a != b:
                    co[a][b] += 1
    return co

def normalize_cooccurrence(co: Dict[int, Dict[int, int]]) -> Dict[int, Dict[int, float]]:
    # 각 행(번호 a)에 대해 최대값으로 나눠 0~1 정규화
    norm = defaultdict(dict)
    for a, row in co.items():
        m = max(row.values()) if row else 1
        for b, v in row.items():
            norm[a][b] = v / m if m > 0 else 0.0
    return norm

def advanced_score(nums: List[int], probs: Dict[int, float], co_norm: Dict[int, Dict[int, float]], prev_nums: List[int]) -> float:
    # (1) 확률합 (2) 상관관계 점수 (3) 반전 보너스 (4) 밴드 보너스
    prob = _prob_score(nums, probs)
    # 상관관계: 조합 내 모든 쌍의 정규화된 공동출현 평균
    pairs = [(a, b) for i, a in enumerate(nums) for b in nums[i+1:]]
    if pairs:
        co_score = float(np.mean([ (co_norm.get(a, {}).get(b, 0.0) + co_norm.get(b, {}).get(a, 0.0)) * 0.5 for a, b in pairs ]))
    else:
        co_score = 0.0
    # 반전번호 보너스: 이전 회차의 (46-n) 중 하나라도 포함 시 +보너스
    mirror = set(46 - n for n in (prev_nums or []))
    has_mirror = len(mirror & set(nums)) > 0
    mirror_bonus = 0.25 if has_mirror else 0.0
    # 합 보너스
    band = _band_bonus(nums)
    # 가중 합
    return prob + 0.6 * co_score + mirror_bonus + 0.15 * band

def generate_advanced_ml_sets(n_sets: int = 10) -> List[List[int]]:
    """
    ML + 상관관계(co-occurrence) + 반전번호(46-n) 강화 버전.
    - 지수감쇠 확률 기반 후보 풀
    - 룰 필터 통과
    - 상관관계 + 반전보너스 + 확률합으로 재랭킹
    - 다양성(중복 숫자 과다)을 억제
    """
    qs = LottoResult.objects.order_by('-draw_no')[:1000]
    history = [r.get_numbers() for r in qs][::-1]
    prev = history[-1] if history else []
    probs = compute_probs(history, half_life=60, smooth=0.5, miss_cap=20)

    # 공동 출현 행렬(정규화)
    co = build_cooccurrence(history)
    co_norm = normalize_cooccurrence(co)

    # 대량 생성
    rerank_cfg = RerankConfig(candidate_pool_size=32, generate_count=max(300, n_sets * 60), pick_top=n_sets, diversity_penalty=0.30)
    pool = [n for n, _ in sorted(probs.items(), key=lambda x: x[1], reverse=True)[:rerank_cfg.candidate_pool_size]]

    rng = np.random.default_rng(97)
    bag, tries = [], 0
    while len(bag) < rerank_cfg.generate_count and tries < rerank_cfg.generate_count * 40:
        tries += 1
        w = np.array([probs[p] for p in pool], dtype=float); w = np.clip(w, 1e-9, None); w /= w.sum()
        cand = sorted(list(rng.choice(pool, size=6, replace=False, p=w)))
        if passes_rules(cand, prev, RuleConfig()):
            bag.append(cand)

    # 중복 제거
    uniq, seen = [], set()
    for c in bag:
        t = tuple(c)
        if t not in seen:
            uniq.append(c); seen.add(t)

    # 고급 스코어로 정렬 + 다양성 페널티 적용해 상위 n_sets 선정
    picked: List[Tuple[float, List[int]]] = []
    for c in sorted(uniq, key=lambda x: -advanced_score(x, probs, co_norm, prev)):
        penalty = 0.0
        for _, p in picked:
            overlap = len(set(c) & set(p))
            penalty += rerank_cfg.diversity_penalty * max(0, overlap - 2)
        picked.append((advanced_score(c, probs, co_norm, prev) - penalty, c))
        if len(picked) >= rerank_cfg.pick_top:
            break

    return [c for _, c in sorted(picked, key=lambda x: -x[0])]

# ──────────────────────────────
# Recent-N(기본 60) 가중 + Overdue 미세 부스팅 추천기 (추가)
# ──────────────────────────────
from dataclasses import dataclass
from typing import Optional

@dataclass
class RecentBoostConfig:
    window_n: int = 60               # 최근 윈도우 크기
    overdue_exp: float = 0.3         # 미출(Overdue) 가중 지수 (가벼운 부스팅)
    candidate_pool_size: int = 45    # 후보 풀(1~45 중 상위 몇 개를 사용할지)
    generate_batch: int = 2000       # 1세트 생성 시 내부 후보 수
    sum_target: int = 155            # Shape 타깃 합계
    # pick 단계는 기존 RerankConfig 사용 (diversity_penalty 등)

def _recent60_probs(history: List[List[int]], cfg: RecentBoostConfig) -> Dict[int, float]:
    """
    최근 window_n 회의 단순 출현 빈도(+1 스무딩)에,
    미출(Overdue) 벡터를 (overdue+1)^overdue_exp 로 미세 보정하여 결합.
    """
    N = 45
    if not history:
        return {i: 6/45 for i in range(1, N+1)}

    # 최근 N회 추출
    recent = history[-cfg.window_n:] if len(history) >= cfg.window_n else history[:]
    # 최근 빈도
    cnt = Counter(x for row in recent for x in row)
    recent_arr = np.array([cnt.get(i, 0) for i in range(1, N+1)], dtype=float) + 1.0  # +1 smoothing

    # 미출(Overdue): 마지막으로 등장한 회차 인덱스 기반
    last_seen = {i: 0 for i in range(1, N+1)}
    for idx, nums in enumerate(history, start=1):
        for n in nums:
            last_seen[n] = idx
    overdue = np.array([len(history) - last_seen[i] for i in range(1, N+1)], dtype=float)
    overdue_boost = (overdue + 1.0) ** max(0.0, cfg.overdue_exp)

    w = recent_arr * overdue_boost
    w = np.clip(w, 1e-8, None)
    # 기대합 ≈ 6으로 정규화
    w = w / w.sum() * 6.0
    return {i: float(w[i-1]) for i in range(1, N+1)}

def _shape_score(nums: List[int], target_sum: int = 155) -> float:
    """합이 target_sum에 근접할수록 가점."""
    return -abs(sum(nums) - target_sum)

def _gumbel_topk_sample(pool: List[int], probs: Dict[int, float], k: int = 6) -> List[int]:
    """
    간단 샘플러: 풀에 대한 확률로 np.random.choice 사용 (중복 없이)
    - Gumbel-top-k 대신, 경량 구현으로 충분히 빠름.
    """
    w = np.array([max(1e-12, probs[p]) for p in pool], dtype=float)
    w = w / w.sum()
    pick = sorted(list(np.random.choice(pool, size=k, replace=False, p=w)))
    return pick

def generate_recent60_boosted_sets(
    n_sets: int = 10,
    cfg_recent: RecentBoostConfig = RecentBoostConfig(),
    cfg_rule: RuleConfig = RuleConfig(),
    rerank: Optional[RerankConfig] = None
) -> List[List[int]]:
    """
    최근 N=60 가중 + Overdue(0.3) 부스팅 기반 추천 10세트.
    - 기존 규칙 필터(passes_rules) 통과
    - Shape(합계) 선호 + 간단 다양성 패널티로 재랭킹
    """
    # 학습 데이터(최신 1000개까지만 사용)는 기존과 동일한 컨벤션 유지
    qs = LottoResult.objects.order_by('-draw_no')[:1000]
    history = [r.get_numbers() for r in qs][::-1]
    prev = history[-1] if history else []

    probs = _recent60_probs(history, cfg_recent)

    # 후보풀: 상위 candidate_pool_size
    pool = [n for n, _ in sorted(probs.items(), key=lambda x: x[1], reverse=True)[:cfg_recent.candidate_pool_size]]

    # 대량 생성
    bag: List[List[int]] = []
    tries = 0
    max_tries = max(20000, cfg_recent.generate_batch * 20)
    rng = np.random.default_rng(1195001)

    while len(bag) < max(200, n_sets*40) and tries < max_tries:
        tries += 1
        cand = _gumbel_topk_sample(pool, probs, k=6)
        if passes_rules(cand, prev, cfg_rule):
            bag.append(cand)

    # 중복 제거
    uniq, seen = [], set()
    for c in bag:
        t = tuple(c)
        if t not in seen:
            uniq.append(c); seen.add(t)

    # 재랭킹 (확률합 + Shape 선호) + 다양성 패널티
    if rerank is None:
        rerank = RerankConfig(candidate_pool_size=len(pool), generate_count=len(uniq), pick_top=n_sets, diversity_penalty=0.25)

    def base_score(nums: List[int]) -> float:
        return _prob_score(nums, probs) + 0.15 * _shape_score(nums, cfg_recent.sum_target)

    picked: List[Tuple[float, List[int]]] = []
    for c in sorted(uniq, key=lambda x: -base_score(x)):
        penalty = 0.0
        for _, p in picked:
            overlap = len(set(c) & set(p))
            penalty += rerank.diversity_penalty * max(0, overlap - 2)
        picked.append((base_score(c) - penalty, c))
        if len(picked) >= rerank.pick_top:
            break

    return [c for _, c in sorted(picked, key=lambda x: -x[0])]
