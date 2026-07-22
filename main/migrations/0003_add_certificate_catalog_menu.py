from django.db import migrations


def add_menu_item(apps, schema_editor):
    MenuItem = apps.get_model("main", "MenuItem")

    parent = MenuItem.objects.filter(title="이력", parent__isnull=True).first()
    if not parent:
        return

    if MenuItem.objects.filter(title="자격증리스트", parent=parent).exists():
        return

    cert_mgmt = MenuItem.objects.filter(title__startswith="자격증관리", parent=parent).first()
    order = (cert_mgmt.order + 1) if cert_mgmt else 37

    MenuItem.objects.create(
        title="자격증리스트",
        parent=parent,
        url="/teachers/certificate-catalog/",
        order=order,
        access_level="teacher",
    )


def remove_menu_item(apps, schema_editor):
    MenuItem = apps.get_model("main", "MenuItem")
    MenuItem.objects.filter(title="자격증리스트", url="/teachers/certificate-catalog/").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0002_alter_menuitem_access_level"),
    ]

    operations = [
        migrations.RunPython(add_menu_item, remove_menu_item),
    ]
