from datetime import timezone
import pandas as pd
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from .models import LessonProgress, ProgramLesson
from courses.models import Program

def progress_home(request):
    """진도관리 메인"""
    programs = Program.objects.all()
    return render(request, "progress/home.html", {"programs": programs})


def lesson_list(request, program_id):
    program = get_object_or_404(Program, id=program_id)
    lessons = ProgramLesson.objects.filter(program=program)

    return render(request, "progress/lesson_list.html", {
        "program": program,
        "lessons": lessons,
    })


def lesson_create(request, program_id):
    program = get_object_or_404(Program, id=program_id)

    if request.method == "POST":
        order = request.POST.get("order")
        title = request.POST.get("title")
        content = request.POST.get("content")

        ProgramLesson.objects.create(
            program=program,
            order=order,
            title=title,
            content=content
        )
        messages.success(request, "차시가 등록되었습니다.")
        return redirect("progress:lesson_list", program_id=program.id)

    return render(request, "progress/lesson_form.html", {"program": program})

def lesson_list(request, program_id):
    program = get_object_or_404(Program, id=program_id)
    lessons = ProgramLesson.objects.filter(program=program).order_by("order")

    return render(request, "progress/lesson_list.html", {
        "program": program,
        "lessons": lessons
    })

def upload_lessons(request, program_id):
    program = get_object_or_404(Program, id=program_id)

    if request.method == "POST" and request.FILES.get("excel"):
        df = pd.read_excel(request.FILES["excel"])

        for _, row in df.iterrows():
            ProgramLesson.objects.update_or_create(
                program=program,
                order=row["order"],
                defaults={
                    "title": row["title"],
                    "content": row.get("content", ""),
                }
            )

        messages.success(request, "엑셀 업로드 완료!")
        return redirect("progress:lesson_list", program_id=program.id)

    return render(request, "progress/upload_lessons.html", {"program": program})



def student_progress(request, program_id):
    student = request.user
    lessons = ProgramLesson.objects.filter(program_id=program_id)

    # LessonProgress 자동 생성
    for lesson in lessons:
        LessonProgress.objects.get_or_create(student=student, lesson=lesson)

    progresses = LessonProgress.objects.filter(student=student, lesson__program_id=program_id)

    if request.method == "POST":
        for lp in progresses:
            checked = request.POST.get(f"lesson_{lp.id}")
            if checked:
                lp.is_completed = True
                lp.completed_at = timezone.now()
            else:
                lp.is_completed = False
                lp.completed_at = None
            lp.save()

        return redirect("progress:student_progress", program_id=program_id)

    return render(request, "progress/student_progress.html", {
        "program": program_id,
        "progresses": progresses
    })