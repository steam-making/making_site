from django.db import migrations

OLD_CATEGORIES = ["창의학습", "안전교육", "자기주도학습"]
NEW_CATEGORY = "방과후"


def _replace_category(value, old, new):
    tokens = [t.strip() for t in value.split(",") if t.strip()]
    tokens = [new if t == old else t for t in tokens]
    # 중복 제거(순서 유지)
    seen = set()
    result = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return ",".join(result)


def forward(apps, schema_editor):
    CertificateCatalogItem = apps.get_model("teachers", "CertificateCatalogItem")
    for old in OLD_CATEGORIES:
        for item in CertificateCatalogItem.objects.filter(category__contains=old):
            item.category = _replace_category(item.category, old, NEW_CATEGORY)
            item.save(update_fields=["category"])


def backward(apps, schema_editor):
    # 되돌릴 수 없는 병합이므로 별도 처리하지 않음
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("teachers", "0017_certificatecatalogitem_course_intro_and_more"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
