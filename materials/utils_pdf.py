# === 파일: materials/utils_pdf.py ===
"""
PDF 생성 공통 유틸 함수 모음
- 한글 폰트 등록
- 한글 금액 변환
- 공급자 정보 구성
- 견적서 제목 자동생성
"""

from __future__ import annotations
import os
from django.conf import settings
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from pathlib import Path

# ---------------------------------------------------------------------
# 1) 한글 폰트 등록
# ---------------------------------------------------------------------
def _ensure_korean_fonts():
    """
    사용할 한글 폰트를 등록하고 (정상/볼드) 폰트 이름을 반환합니다.
    우선순위: 시스템 설치(Nanum) > 프로젝트 포함 경로(assets/fonts)
    """
    candidates = [
        # Ubuntu 등 리눅스에 fonts-nanum 설치된 경우
        ('NanumGothic', '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
         'NanumGothic-Bold', '/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf'),
        # 프로젝트 포함 경로
        ('NanumGothic', os.path.join(getattr(settings, 'BASE_DIR', ''), 'assets', 'fonts', 'NanumGothic.ttf'),
         'NanumGothic-Bold', os.path.join(getattr(settings, 'BASE_DIR', ''), 'assets', 'fonts', 'NanumGothicBold.ttf')),
    ]

    for normal_name, normal_path, bold_name, bold_path in candidates:
        if os.path.exists(normal_path) and os.path.exists(bold_path):
            # 이미 등록된 경우 예외가 날 수 있어 try 처리
            try:
                pdfmetrics.registerFont(TTFont(normal_name, normal_path))
            except Exception:
                pass
            try:
                pdfmetrics.registerFont(TTFont(bold_name, bold_path))
            except Exception:
                pass
            try:
                registerFontFamily(
                    normal_name,
                    normal=normal_name,
                    bold=bold_name,
                    italic=normal_name,
                    boldItalic=bold_name
                )
            except Exception:
                pass
            return normal_name, bold_name

    # 최후 수단(한글 미지원이지만 오류 방지)
    return 'Helvetica', 'Helvetica-Bold'


# ---------------------------------------------------------------------
# 2) 숫자 → 한글 금액 (“일금…원정”)
# ---------------------------------------------------------------------
_HANGUL_NUMS = ['영','일','이','삼','사','오','육','칠','팔','구']
_HANGUL_UNITS_SMALL = ['','십','백','천']
_HANGUL_UNITS_LARGE = ['','만','억','조']

def number_to_korean_amount(n: int) -> str:
    """
    123456789 -> '일금일억이천삼백사십오만육천칠백팔십구원정'
    0 -> '일금영원정'
    """
    if int(n) == 0:
        return "일금영원정"
    s = str(int(n))
    groups = []
    while s:
        groups.append(s[-4:])
        s = s[:-4]
    words = []
    for i, grp in enumerate(groups):
        grp = grp.zfill(4)
        seg = []
        for j, ch in enumerate(grp):
            d = int(ch)
            if d == 0:
                continue
            unit_small = _HANGUL_UNITS_SMALL[3 - j]
            # '일십','일백','일천'의 '일'은 생략
            if d == 1 and unit_small != '':
                seg.append(unit_small)
            else:
                seg.append(_HANGUL_NUMS[d] + unit_small)
        if seg:
            words.insert(0, ''.join(seg) + _HANGUL_UNITS_LARGE[i])
    return f"일금{''.join(words)}원정"


# ---------------------------------------------------------------------
# 3) 금액 포맷
# ---------------------------------------------------------------------
def fmt_money(v) -> str:
    """정수 금액을 '1,234원' 형식으로."""
    return f"{int(v):,}원"


# ---------------------------------------------------------------------
# 4) 공급자 정보(환경설정 병합)
# ---------------------------------------------------------------------

# 특정 학교 목록
SPECIAL_INSTITUTIONS = ["화정남초등학교", "화개초등학교", "효천초등학교"]

def _vendor_info(institution=None) -> dict:
    """
    기관별로 공급자 정보를 반환합니다.
    - 특정 학교(화정남초등학교, 화개초등학교, 효천초등학교)는 별도 공급자 정보 사용
    - 그 외는 settings.ESTIMATE_VENDOR 와 defaults 병합
    """
    # 특정 학교 전용 공급자 정보
    if institution and institution.name in SPECIAL_INSTITUTIONS:
        return {
            "business_no": "408-18-51106",
            "name": "N Robotics",
            "address": "광주광역시 남구 서문대로 771 2층",
            "biz_type": "도소매",
            "tel": "062-651-3590",
            "mobile": "010-8789-3590",
            "bank": "국민 792001-01-310167",
            "logo_path": None,
            "ceo": "나윤제",
            "fax": "-",   # ✅ 누락된 키 추가 (값 없으면 기본 '-'),
            "logo_path": str(Path(settings.BASE_DIR) / "static" / "images" / "nrobotics_stamp.png"),
        }

    # 기본 공급자 정보 (settings.ESTIMATE_VENDOR)
    defaults = {
        "business_no": "420-03-01408",
        "name": "메듀테크",
        "address": "광주광역시 서구 화개중앙로 51 5층",
        "biz_type": "도소매, 서비스",
        "tel": "062-365-1553",
        "mobile": "010-9890-1553",
        "bank": "국민 772601-01-707471",
        "logo_path": None,
        "ceo": "박종석",
        "fax": "0504-432-1553",  # ✅ 기본값에도 포함
        "logo_path": str(Path(settings.BASE_DIR) / "static" / "images" / "making_stamp.png"),
    }
    conf = getattr(settings, "ESTIMATE_VENDOR", {}) or {}
    return {**defaults, **conf}


# ---------------------------------------------------------------------
# 5) 견적서 제목 생성
# ---------------------------------------------------------------------
def _make_estimate_title(institution, order_month: str) -> str:
    """
    규칙: '주문년월 + 프로그램명 + 기관명 + 견적서'
    ※ 주의: program/name 순서가 뒤바뀌지 않도록 함.
    """
    program_name = getattr(institution, "program", "") or ""
    institution_name = getattr(institution, "name", "") or ""
    title = f"{order_month} {program_name} {institution_name} 견적서"
    # 공백 정리
    return " ".join(title.split())
