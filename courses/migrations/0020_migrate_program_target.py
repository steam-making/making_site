from django.db import migrations

def migrate_target_code_to_fk(apps, schema_editor):
    Program = apps.get_model("courses", "Program")
    Target = apps.get_model("courses", "Target")

    code_to_id = {t.code: t.id for t in Target.objects.all()}

    for program in Program.objects.all().only("id", "target"):
        code = getattr(program, "target", None)
        if code and code in code_to_id:
            Program.objects.filter(id=program.id).update(target_id=code_to_id[code])
        else:
            Program.objects.filter(id=program.id).update(target_id=None)

class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0019_target_alter_program_target"),
    ]

    operations = [
        migrations.RunPython(migrate_target_code_to_fk, reverse_code=migrations.RunPython.noop),
    ]
