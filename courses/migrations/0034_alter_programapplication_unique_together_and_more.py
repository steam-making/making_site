import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_alter_profile_birth_date'),
        ('courses', '0033_program_end_date'),
    ]

    operations = [
        # ⚠️ 기존 unique_together 제거는 생략 (이미 없음)
        migrations.RunSQL(sql="", reverse_sql=""),

        # ✅ program_class 필드 추가
        migrations.AddField(
            model_name='programapplication',
            name='program_class',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='applications',
                to='courses.programclass',
            ),
        ),
    ]
