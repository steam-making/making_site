import requests
from django.core.management.base import BaseCommand
from schools.models import School
from datetime import datetime

API_URL = "https://www.schoolinfo.go.kr/openApi.do"
API_KEY = "2a33c7c70e384d4093abacf7471edf42"

CURRENT_YEAR = str(datetime.now().year)

# 광주 + 전남 시군구
GU_LIST = [
    ("29", "29110"), ("29", "29140"), ("29", "29155"),
    ("29", "29170"), ("29", "29200"),

    #담양,곡성,고흥
    ("46", "46710"), ("46", "46720"), ("46", "46770"),
    #장흥, 무안, 여수
    ("46", "46800"), ("46", "46840"), ("46", "46130"),
    #나주, 보성, 화순
    ("46", "46170"), ("46", "46780"), ("46", "46790"),
    #영암, 영광, 완도
    ("46", "46830"), ("46", "46870"), ("46", "46890"),
    #진도, 해남, 광양
    ("46", "46900"), ("46", "46820"), ("46", "46230"),
    #신안, 강진, 함평
    ("46", "46910"), ("46", "46810"), ("46", "46860"),
    #장성, 목포, 순천
    ("46", "46880"), ("46", "46110"), ("46", "46150"),
    #구례
    ("46", "46730"),
]

KIND_CODES = {
    "02": "초등학교",
    "03": "중학교",
    "04": "고등학교",
}


class Command(BaseCommand):
    help = "학교알리미 API 기반 학교 데이터 업데이트 (기본정보 + 학생수 문자열 저장)"

    def fetch_school_list(self, sido, sgg, kind):
        params = {
            "apiKey": API_KEY,
            "apiType": "0",
            "pbanYr": CURRENT_YEAR,
            "sidoCode": sido,
            "sggCode": sgg,
            "schulKndCode": kind,
        }
        res = requests.get(API_URL, params=params)
        text = res.text

        if not text.strip().startswith("{"):
            return []

        data = res.json()
        if data.get("resultCode") != "success":
            return []

        return data.get("list", [])

    def fetch_student_list(self, sido, sgg, kind):
        params = {
            "apiKey": API_KEY,
            "apiType": "62",
            "pbanYr": CURRENT_YEAR,
            "sidoCode": sido,
            "sggCode": sgg,
            "schulKndCode": kind,
        }
        res = requests.get(API_URL, params=params)
        text = res.text

        if not text.strip().startswith("{"):
            return {}

        data = res.json()
        if data.get("resultCode") != "success":
            return {}

        stu_map = {}
        for row in data.get("list", []):
            code = row.get("SCHUL_CODE")
            stu_map[code] = row.get("COL_FGR_SUM", "")   # 🔥 그대로 저장 (111(6) 같은 값)

        return stu_map

    def handle(self, *args, **kwargs):
        total = 0

        for sido, sgg in GU_LIST:
            self.stdout.write(f"\n📌 시도 {sido}, 시군구 {sgg}")

            for kind_code, kind_name in KIND_CODES.items():
                self.stdout.write(f"  ▶ {kind_name} 조회 중…")

                info_list = self.fetch_school_list(sido, sgg, kind_code)
                stu_map = self.fetch_student_list(sido, sgg, kind_code)

                if not info_list:
                    self.stdout.write("   ❌ 데이터 없음")
                    continue

                for item in info_list:
                    code = item.get("SCHUL_CODE")
                    student_str = stu_map.get(code, "")

                    School.objects.update_or_create(
                        school_code=code,
                        defaults={
                            "name": item.get("SCHUL_NM"),
                            "address": item.get("SCHUL_RDNMA", ""),
                            "homepage": item.get("HMPG_ADRES", ""),
                            "zipcode": item.get("SCHUL_RDNZC", "").strip(),
                            "office_phone": item.get("USER_TELNO", ""),
                            "student_count": student_str,  # 🔥 문자열 그대로 저장
                        }
                    )
                    total += 1

        self.stdout.write(
            self.style.SUCCESS(f"\n🎉 총 {total}개 학교 업데이트 완료!")
        )
