from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_profile_withdrawal_requested'),  # ✅ Child 모델이 있는 앱의 최신 migration 맞게 수정
        ('courses', '0001_initial'),             
    ]

    operations = [
        migrations.AddField(
            model_name='programapplication',
            name='child',
            field=models.ForeignKey(
                to='accounts.child',
                on_delete=django.db.models.deletion.CASCADE,
                null=True,    # ✅ 기존 데이터 보호 위해 null 허용
                blank=True,
                related_name='applications'
            ),
        ),
    ]
