import openpyxl
from courses.models import ProgramSyllabus


def import_syllabus_from_excel(program, excel_file):
    wb = openpyxl.load_workbook(excel_file)
    ws = wb.active

    # 기존 계획서 삭제 (덮어쓰기)
    ProgramSyllabus.objects.filter(program=program).delete()

    for row in ws.iter_rows(min_row=2, values_only=True):
        week, title, content, material, note = row

        if not week or not title:
            continue

        ProgramSyllabus.objects.create(
            program=program,
            week=int(week),
            title=str(title),
            content=str(content),
            material=str(material) if material else "",
            note=str(note) if note else "",
        )
