import re
from django.utils.safestring import mark_safe
from .constants import DEPARTMENT_KEYWORD_MAP, DEPARTMENT_COLORS, WEEKDAY_COLORS


def normalize(text: str) -> str:
    """
    공백/특수문자 제거 + 소문자 변환
    """
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w가-힣]", "", text)
    return text


def highlight_department(title, department, keyword_map, color_map):
    """
    제목에서 부서 키워드 강조
    - 이미 강조된 텍스트는 재처리하지 않음
    - 긴 키워드 우선
    """

    if not title:
        return title

    highlighted = title

    # 🔹 강조 대상 부서 결정
    if department and department in keyword_map:
        departments = [department]
    else:
        departments = keyword_map.keys()

    for dep in departments:
        color = color_map.get(dep, "secondary")
        keywords = keyword_map.get(dep, [])

        # 🔥 긴 키워드 먼저 (로봇과학 → 로봇)
        for kw in sorted(keywords, key=len, reverse=True):
            # ✅ 이미 span 안에 있으면 건너뜀
            pattern = rf'(?<!>)({re.escape(kw)})(?![^<]*</span>)'

            highlighted = re.sub(
                pattern,
                rf'<span class="dept-badge bg-{color}">\1</span>',
                highlighted
            )

    return mark_safe(highlighted)

def extract_program_keywords_from_title(title):
    """
    제목에서 실제 프로그램명(로봇과학, 로봇코딩 등)을 추출
    → TeachingInstitution.program 과 직접 비교용
    """
    title_norm = normalize(title)
    matched = set()

    for dep, keywords in DEPARTMENT_KEYWORD_MAP.items():
        for kw in sorted(keywords, key=len, reverse=True):
            if normalize(kw) in title_norm:
                matched.add(kw)

    return list(matched)

def render_weekday_badges(weekday_str):
    """
    '월, 화, 목' → badge HTML로 변환
    """
    if not weekday_str:
        return ""

    days = [d.strip() for d in weekday_str.split(",")]
    html = []

    for d in days:
        color = WEEKDAY_COLORS.get(d, "secondary")
        html.append(
            f'<span class="badge bg-{color} me-1">{d}</span>'
        )

    return " ".join(html)
