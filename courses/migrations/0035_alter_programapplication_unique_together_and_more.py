from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_alter_profile_birth_date'),
        ('courses', '0034_alter_programapplication_unique_together_and_more'),
    ]

    operations = [
        # ✅ 새로운 UniqueConstraint 추가
        migrations.AddConstraint(
            model_name='programapplication',
            constraint=models.UniqueConstraint(
                fields=('program', 'program_class', 'child'),
                name='unique_program_class_child',
            ),
        ),
    ]
