from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0036_remove_programapplication_unique_program_class_child'),
        
    ]

    operations = [
        # ⚠️ DB에 이미 program_class_id 컬럼이 존재하므로
        # AddField 대신에 그냥 통과용(아무 작업 안 함)으로 둠.
        migrations.RunSQL(sql="", reverse_sql=""),
    ]
