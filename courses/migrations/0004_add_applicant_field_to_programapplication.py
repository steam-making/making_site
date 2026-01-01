from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_profile_withdrawal_requested'),  # ✅ accounts 최신 migration 번호로 수정
        ('courses', '0003_alter_programapplication_child'),
    ]

    operations = [
        migrations.AddField(
            model_name='programapplication',
            name='applicant',
            field=models.ForeignKey(
                to='accounts.profile',
                on_delete=django.db.models.deletion.CASCADE,
                null=True,   # ✅ 기존 데이터 보호 위해 NULL 허용
                blank=True,
                related_name='applications'
            ),
        ),
    ]
