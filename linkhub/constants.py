DEPARTMENT_KEYWORD_MAP = {
    "로봇": [
        "로봇과학",
        "로봇코딩",
        "로봇조립",
        "로봇제작",
        "로봇공학",
        "로봇",   # ← 로봇에 포함
    ],
    "과학": [
        "과학탐구",
        "과학실험",
        "생명과학",
        "융합과학",
    ],
    "창의수학": [
        "수학",
        "창의수학",
        "사고력수학",
    ],
    "3D펜": [
        "3D펜톡",
        "3D펜",
    ],
    "항공드론": [
        "드론항공",
        "항공드론",
        "드론",
        "항공",
    ],
    "컴퓨터": [
        "컴퓨터",
        "코딩",
        "프로그래밍",
        "AI",
    ],
}

DEPARTMENT_COLORS = {
    "로봇": "primary",      # 파랑
    "과학": "success",      # 초록
    "창의수학": "warning",  # 노랑
    "3D펜": "info",         # 하늘
    "항공드론": "danger",   # 빨강
    "컴퓨터": "dark",       # 검정
}

# 라디오 버튼용
DEPARTMENT_KEYWORDS = list(DEPARTMENT_KEYWORD_MAP.keys())


WEEKDAY_COLORS = {
    "월": "primary",     # 파랑
    "화": "success",     # 초록
    "수": "warning",     # 노랑
    "목": "info",        # 하늘
    "금": "danger",      # 빨강
}
