from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0031_materialrelease_created_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='materialrelease',
            name='source_type',
            field=models.CharField(blank=True, choices=[('', '일반'), ('levelup_auto', '단계업 자동생성')], default='', max_length=20, verbose_name='생성 경로'),
        ),
    ]
