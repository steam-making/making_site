from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0037_programapplication_unique_program_class_child'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='programapplication',
            constraint=models.UniqueConstraint(
                fields=('program', 'program_class', 'child'),
                name='unique_program_class_child'
            ),
        ),
    ]
