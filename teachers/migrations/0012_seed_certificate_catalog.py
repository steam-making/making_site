from django.db import migrations


def _curriculum(*lines):
    return "\n".join(lines)


CATALOG_SEED = [
    {
        "category": "코딩", "auth_type": "민간", "name": "코딩지도사2급", "issuer": "청소년로봇연맹",
        "validity": "10년(종료 시 1회 연장가능)", "issue_fee": "60000", "education_fee": "200000",
        "materials": "엔트리 스타터", "min_students": "1명 이상", "session_length": "90분", "session_count": 4,
    },
    {
        "category": "코딩", "auth_type": "민간", "name": "코딩지도사1급", "issuer": "청소년로봇연맹",
        "validity": "10년(종료 시 1회 연장가능)", "issue_fee": "80000", "education_fee": "200000",
        "materials": "엔트리 메이커", "min_students": "1명 이상", "session_length": "90분", "session_count": 4,
    },
    {
        "category": "로봇", "auth_type": "민간", "name": "로봇코딩지도사2급", "issuer": "청소년로봇연맹",
        "validity": "10년(종료 시 1회 연장가능)", "issue_fee": "60000", "education_fee": "250000",
        "materials": "올로AI Lv1", "min_students": "1명 이상", "session_length": "90분", "session_count": 4,
        "curriculum": _curriculum(
            "로봇교구 부품 알기 / 로봇 어원 및 3원칙 / 올로AI 1단계 로봇 소개 / 목도리 도마뱀 제작 / 스팀컵 앱 소개 및 활용",
            "올로AI 2단계 로봇 소개 / 애벌레 로봇제작 / 적외선 센서 이해 및 코딩",
            "올로AI 3단계 로봇 소개 / 트레일러 로봇 제작 / 라인트레이싱 코딩",
            "필기 + 실기 시험",
        ),
    },
    {
        "category": "로봇", "auth_type": "민간", "name": "로봇코딩지도사1급", "issuer": "청소년로봇연맹",
        "validity": "10년(종료 시 1회 연장가능)", "issue_fee": "80000", "education_fee": "250000",
        "materials": "올로AI Lv2", "min_students": "1명 이상", "session_length": "90분", "session_count": 4,
        "curriculum": _curriculum(
            "올로AI 4단계 로봇 소개 / 지게차 제작 / 다이나믹셀 활용하기",
            "올로AI 5단계 로봇 소개 / 하키로봇 제작",
            "필기 + 실기 시험",
        ),
    },
    {
        "category": "3D펜", "auth_type": "민간", "name": "3D펜지도사-일반과정", "issuer": "3D프린팅펜 창의융합교육협회",
        "issue_fee": "60000", "education_fee": "200000",
        "materials": "3D펜(1대) & 지도사과정교재", "min_students": "1명 이상", "session_length": "90분", "session_count": 4,
        "curriculum": _curriculum(
            "3D프린팅펜의 개념과 원리 / 실습(기본 팁, 안전교육) / 실습(다양한 크기의 점) / 실습(선의 다양한 표현과 활용) / 완성작품: 새 학년 새 마음",
            "3D프린팅펜과 교육 / 실습(선과 면의 활용, 면채우기) / 완성작품: 홀로그램상영관, 손잡이 홀더",
            "3D펜 지도사 필기 시험 / 실습(면의 다양한 표현과 활용) / 완성작품: 반딧불이",
            "3D프린팅펜 수업준비 / 운영 및 수업 자료 / 수료",
        ),
    },
    {
        "category": "3D펜", "auth_type": "민간", "name": "3D펜지도사-수석과정", "issuer": "3D프린팅펜 창의융합교육협회",
        "issue_fee": "60000", "education_fee": "700000",
        "materials": "교구재비 40,000원", "min_students": "8명 이상",
        "curriculum": _curriculum(
            "중요 기초 되돌아보기",
            "3D펜과의 예술의 만남",
            "다양한 3D펜 표현방법",
            "복합 매체를 활용한 3D 예술 작품 제작",
            "수업 활용 TIP",
        ),
    },
    {
        "category": "과학", "auth_type": "민간", "name": "생명과학지도사", "issuer": "과학나무",
        "validity": "2년 (연장 가능)", "issue_fee": "40000", "education_fee": "200000",
        "materials": "생명과학 & 실험과학", "min_students": "1명 이상", "session_length": "90분", "session_count": 4,
        "curriculum": _curriculum(
            "지도사 및 수업 소개, 교구 활용1",
            "교구 활용2",
            "생명/과학 지도사 수업 방법",
            "생명/과학 지도사 필기 테스트",
        ),
    },
    {
        "category": "과학", "auth_type": "민간", "name": "융합과학지도사", "issuer": "과학나무",
        "validity": "2년 (연장 가능)", "issue_fee": "40000", "education_fee": "200000",
        "materials": "생명과학 & 실험과학", "min_students": "1명 이상", "session_length": "90분", "session_count": 4,
        "curriculum": _curriculum(
            "지도사 및 수업 소개, 교구 활용1",
            "교구 활용2",
            "생명/과학 지도사 수업 방법",
            "생명/과학 지도사 필기 테스트",
        ),
    },
    {
        "category": "드론", "auth_type": "민간", "name": "드론지도사1급", "issuer": "청소년로봇연맹",
        "validity": "10년(종료 시 1회 연장가능)", "issue_fee": "80000", "education_fee": "200000",
        "materials": "글라이더2 + 전동2 + 드론(100000)", "min_students": "1명 이상", "session_length": "90분", "session_count": 4,
    },
    {
        "category": "방과후", "auth_type": "민간", "name": "방과후지도사1급",
        "issuer": "선택사항 (ex:한국직업능력진흥원 http://pqi.kr/)",
        "exam_type": "온라인수강 및 필기시험 (강의기간 약6주정도 소요)", "exam_fee": "-", "issue_fee": "대략 80,000~85,000",
    },
    {
        "category": "창의학습", "auth_type": "민간", "name": "창의학습지도사1급",
        "issuer": "선택사항 (ex:한국직업능력진흥원 http://pqi.kr/)",
        "exam_type": "온라인수강 및 필기시험 (강의기간 약6주정도 소요)", "exam_fee": "-", "issue_fee": "대략 80,000~85,000",
    },
    {
        "category": "안전교육", "auth_type": "민간", "name": "안전교육지도사1급",
        "issuer": "선택사항 (ex:한국직업능력진흥원 http://pqi.kr/)",
        "exam_type": "온라인수강 및 필기시험 (강의기간 약6주정도 소요)", "exam_fee": "-", "issue_fee": "대략 80,000~85,000",
    },
    {
        "category": "자기주도학습", "auth_type": "민간", "name": "자기주도학습지도사1급",
        "issuer": "선택사항 (ex:한국직업능력진흥원 http://pqi.kr/)",
        "exam_type": "온라인수강 및 필기시험 (강의기간 약6주정도 소요)", "exam_fee": "-", "issue_fee": "대략 80,000~85,000",
    },
    {
        "category": "코딩", "auth_type": "민간", "name": "COS 1급", "issuer": "YBM IT",
        "exam_type": "실기", "exam_fee": "20,000~25,000", "issue_fee": "6,000",
    },
    {
        "category": "코딩", "auth_type": "민간", "name": "COS 2급", "issuer": "YBM IT",
        "exam_type": "실기", "exam_fee": "20,000~25,000", "issue_fee": "6,000",
    },
    {
        "category": "코딩", "auth_type": "민간", "name": "COS 3급", "issuer": "YBM IT",
        "exam_type": "실기", "exam_fee": "20,000~25,000", "issue_fee": "6,000",
    },
    {
        "category": "코딩", "auth_type": "민간", "name": "COS 4급", "issuer": "YBM IT",
        "exam_type": "실기", "exam_fee": "20,000~25,000", "issue_fee": "6,000",
    },
    {
        "category": "코딩", "auth_type": "민간", "name": "COS Pro 1급", "issuer": "YBM IT",
        "exam_type": "실기", "exam_fee": "30,000~45,000", "issue_fee": "2,000",
    },
    {
        "category": "코딩", "auth_type": "민간", "name": "COS Pro 2급", "issuer": "YBM IT",
        "exam_type": "실기", "exam_fee": "30,000~45,000", "issue_fee": "2,000",
    },
    {
        "category": "코딩", "auth_type": "민간", "name": "COS Pro 3급", "issuer": "YBM IT",
        "exam_type": "실기", "exam_fee": "30,000~45,000", "issue_fee": "2,000",
    },
    {
        "category": "코딩", "auth_type": "민간", "name": "COS Pro 4급", "issuer": "YBM IT",
        "exam_type": "실기", "exam_fee": "30,000~45,000", "issue_fee": "2,000",
    },
    {
        "category": "코딩", "auth_type": "민간", "name": "CODE Creator", "issuer": "한국창의교육개발원",
        "exam_type": "실기",
    },
    {
        "category": "사무/IT", "auth_type": "국가공인", "name": "워드프로세서1급", "issuer": "대한상공회의소",
        "exam_type": "필기&실기",
    },
    {
        "category": "사무/IT", "auth_type": "국가공인", "name": "워드프로세서2급", "issuer": "대한상공회의소",
        "exam_type": "필기&실기",
    },
    {
        "category": "사무/IT", "auth_type": "국가공인", "name": "정보처리기사", "issuer": "한국산업인력공단",
        "exam_type": "필기&실기",
    },
]


def seed_catalog(apps, schema_editor):
    CertificateCatalogItem = apps.get_model("teachers", "CertificateCatalogItem")
    if CertificateCatalogItem.objects.exists():
        return
    for index, data in enumerate(CATALOG_SEED):
        CertificateCatalogItem.objects.create(order=index, **data)


def unseed_catalog(apps, schema_editor):
    CertificateCatalogItem = apps.get_model("teachers", "CertificateCatalogItem")
    names = [item["name"] for item in CATALOG_SEED]
    CertificateCatalogItem.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("teachers", "0011_certificatecatalogitem"),
    ]

    operations = [
        migrations.RunPython(seed_catalog, unseed_catalog),
    ]
