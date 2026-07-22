import re
from datetime import timedelta

from django.db import migrations
from django.utils import timezone

NEW_SCIENCE_NAME = "생명&융합과학지도사"

DIRECT_CERT_NAMES = [
    "코딩지도사2급",
    "코딩지도사1급",
    "로봇코딩지도사2급",
    "로봇코딩지도사1급",
    "3D펜지도사-일반과정",
    "3D펜지도사-수석과정",
    NEW_SCIENCE_NAME,
    "드론지도사1급",
]


def _curriculum_list(text):
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


def _parse_material_cost(materials_text):
    if not materials_text:
        return 0
    match = re.search(r'([\d,]+)\s*원', materials_text)
    if match:
        return int(match.group(1).replace(",", ""))
    return 0


def _to_int(value):
    try:
        return int(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return 0


def link_instructor_courses(apps, schema_editor):
    CertificateCatalogItem = apps.get_model("teachers", "CertificateCatalogItem")
    Certificate = apps.get_model("teachers", "Certificate")
    InstructorCourseType = apps.get_model("recruit", "InstructorCourseType")
    InstructorRecruit = apps.get_model("recruit", "InstructorRecruit")

    # 1) 생명과학지도사 + 융합과학지도사 -> 생명&융합과학지도사 로 병합 (이미 병합되어 있으면 건드리지 않음)
    life = CertificateCatalogItem.objects.filter(name="생명과학지도사").first()
    fusion = CertificateCatalogItem.objects.filter(name="융합과학지도사").first()
    if life and fusion:
        Certificate.objects.filter(name__in=["생명과학지도사", "융합과학지도사"]).update(name=NEW_SCIENCE_NAME)
        life.name = NEW_SCIENCE_NAME
        life.save(update_fields=["name"])
        fusion.delete()
    elif life and not CertificateCatalogItem.objects.filter(name=NEW_SCIENCE_NAME).exists():
        Certificate.objects.filter(name="생명과학지도사").update(name=NEW_SCIENCE_NAME)
        life.name = NEW_SCIENCE_NAME
        life.save(update_fields=["name"])
    elif fusion and not CertificateCatalogItem.objects.filter(name=NEW_SCIENCE_NAME).exists():
        Certificate.objects.filter(name="융합과학지도사").update(name=NEW_SCIENCE_NAME)
        fusion.name = NEW_SCIENCE_NAME
        fusion.save(update_fields=["name"])

    # 2) 3D펜지도사-일반과정은 기존 "3D펜지도사-일반" 공고를 그대로 연결
    item = CertificateCatalogItem.objects.filter(name="3D펜지도사-일반과정").first()
    if item and not item.related_recruit_id:
        existing_recruit = (
            InstructorRecruit.objects.filter(course_type__name="3D펜지도사-일반")
            .order_by("-created_at")
            .first()
        )
        if existing_recruit:
            item.related_recruit_id = existing_recruit.id
            item.save(update_fields=["related_recruit"])

    # 3) 나머지 직접 교육/발급 가능 자격증들은 신규 InstructorCourseType + InstructorRecruit 생성 후 연결
    now = timezone.now()
    for name in DIRECT_CERT_NAMES:
        if name == "3D펜지도사-일반과정":
            continue

        item = CertificateCatalogItem.objects.filter(name=name).first()
        if not item or item.related_recruit_id:
            continue

        course_type, _ = InstructorCourseType.objects.get_or_create(
            name=item.name,
            defaults={
                "course_intro": f"{item.name} 과정으로, {item.issuer}에서 인증하는 지도사 자격을 취득할 수 있습니다.",
                "educational_goal": f"{item.category} 분야를 현장에서 효과적으로 지도할 수 있는 역량을 기르는 것을 목표로 합니다.",
                "curriculum": [
                    {"session": str(i + 1), "content": line, "time": "1"}
                    for i, line in enumerate(_curriculum_list(item.curriculum))
                ],
                "certificate_agency": item.issuer,
                "certificate_type": "private",
                "cost_education": _to_int(item.education_fee),
                "cost_certificate": _to_int(item.issue_fee),
                "cost_material": _parse_material_cost(item.materials),
                "cost_includes_all": False,
                "benefits": "자격증 발급, 교육자료 제공",
            },
        )

        recruit = InstructorRecruit.objects.create(
            course_type=course_type,
            title=f"{item.name} 1기",
            class_days="",
            class_time="",
            course_intro=course_type.course_intro,
            educational_goal=course_type.educational_goal,
            curriculum=course_type.curriculum,
            certificate_agency=course_type.certificate_agency,
            certificate_type=course_type.certificate_type,
            cost_education=course_type.cost_education,
            cost_certificate=course_type.cost_certificate,
            cost_material=course_type.cost_material,
            cost_includes_all=course_type.cost_includes_all,
            benefits=course_type.benefits,
            recruit_start=now,
            recruit_end=now + timedelta(days=90),
            capacity=0,
            status="open",
        )

        item.related_recruit_id = recruit.id
        item.save(update_fields=["related_recruit"])


class Migration(migrations.Migration):

    dependencies = [
        ("teachers", "0014_certificatecatalogitem_related_recruit"),
        ("recruit", "0019_instructorrecruit_class_days_and_more"),
    ]

    operations = [
        migrations.RunPython(link_instructor_courses, migrations.RunPython.noop),
    ]
