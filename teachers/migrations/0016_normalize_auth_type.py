from django.db import migrations


def normalize_forward(apps, schema_editor):
    CertificateCatalogItem = apps.get_model("teachers", "CertificateCatalogItem")
    CertificateCatalogItem.objects.filter(auth_type="민간").update(auth_type="민간자격")


def normalize_backward(apps, schema_editor):
    CertificateCatalogItem = apps.get_model("teachers", "CertificateCatalogItem")
    CertificateCatalogItem.objects.filter(auth_type="민간자격").update(auth_type="민간")


class Migration(migrations.Migration):

    dependencies = [
        ("teachers", "0015_link_instructor_courses"),
    ]

    operations = [
        migrations.RunPython(normalize_forward, normalize_backward),
    ]
