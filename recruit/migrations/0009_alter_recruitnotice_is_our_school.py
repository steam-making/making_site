from django.db import migrations

def link_school(apps, schema_editor):
    TeachingInstitution = apps.get_model('teachers', 'TeachingInstitution')
    School = apps.get_model('schools', 'School')

    for inst in TeachingInstitution.objects.all():
        if not inst.name:
            continue

        school = School.objects.filter(
            name__iexact=inst.name.strip()
        ).first()

        if school:
            inst.school = school
            inst.save(update_fields=["school"])

class Migration(migrations.Migration):

    dependencies = [
        ('recruit', '0008_recruitnotice_is_our_school'),
    ]

    operations = [
        migrations.RunPython(link_school),
    ]
