from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Case, When, Value, IntegerField
from .models import Task, WorkType
from .forms import TaskForm
from datetime import date


@login_required
def task_list(request):
    selected_work_type = request.GET.get('work_type', '')
    work_types = WorkType.objects.all().order_by('order')

    tasks = Task.objects.filter(created_by=request.user)

    # ✅ 업무종류 필터
    if selected_work_type:
        tasks = tasks.filter(work_type__id=selected_work_type)

    # ✅ 정렬
    tasks = tasks.annotate(
        has_due=Case(
            When(due_date__isnull=False, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by('completed', '-has_due', 'due_date', '-created_at')

    # ✅ 마감 상태별 색상 계산
    today = date.today()
    for t in tasks:
        if t.completed:
            t.row_class = "table-secondary"      # 완료됨 (회색)
        elif not t.due_date:
            t.row_class = "table-info"           # 마감일 없음 (파랑)
        elif t.due_date < today:
            t.row_class = "table-danger"         # 마감 지남 (빨강)
        elif (t.due_date - today).days <= 3:
            t.row_class = "table-warning"        # 마감 임박 (노랑)
        else:
            t.row_class = ""                     # 일반 항목

    return render(request, 'tasks/task_list.html', {
        'tasks': tasks,
        'work_types': work_types,
        'selected_work_type': selected_work_type,
    })


@login_required
def task_create(request):
    """할일 등록"""
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            return redirect('task_list')
    else:
        form = TaskForm()
    return render(request, 'tasks/task_form.html', {'form': form})


@login_required
def task_update(request, pk):
    """할일 수정"""
    task = get_object_or_404(Task, pk=pk, created_by=request.user)
    form = TaskForm(request.POST or None, instance=task)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect('task_list')
    return render(request, 'tasks/task_form.html', {'form': form})


@login_required
def task_delete(request, pk):
    """할일 삭제"""
    task = get_object_or_404(Task, pk=pk, created_by=request.user)
    if request.method == "POST":
        task.delete()
        return redirect('task_list')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
def task_complete(request, pk):
    """할일 완료 처리 + 반복 주기 설정 시 다음 업무 자동 생성"""
    task = get_object_or_404(Task, pk=pk, created_by=request.user)

    # 완료 처리
    task.completed = True
    task.completed_at = timezone.now()
    task.save()

    # ✅ 반복 주기가 설정된 업무면 다음 주기의 새 Task 자동 생성
    if task.repeat != 'none':
        task.create_next_task_if_repeated()

    return redirect('task_list')
