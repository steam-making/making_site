from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='withdrawal_requested',
            field=models.BooleanField(default=False),
        ),
    ]
