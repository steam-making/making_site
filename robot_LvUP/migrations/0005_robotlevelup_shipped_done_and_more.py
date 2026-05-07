from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("robot_LvUP", "0004_remove_robotlevelup_school_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="robotlevelup",
            name="shipped_date",
            field=models.DateField(blank=True, null=True, verbose_name="실출고일"),
        ),
        migrations.AddField(
            model_name="robotlevelup",
            name="shipped_done",
            field=models.BooleanField(default=False, verbose_name="실출고완료"),
        ),
    ]
