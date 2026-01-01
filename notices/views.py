from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.shortcuts import get_object_or_404, redirect, render
from .models import Notice
from .forms import NoticeForm

def is_staff(user):
    return user.is_staff or user.is_superuser

def notice_list(request):
    q = request.GET.get("q", "")
    audience = request.GET.get("audience", "")
    qs = Notice.objects.all()

    # 비스태프는 게시글만
    if not request.user.is_authenticated or not is_staff(request.user):
        qs = qs.filter(status="published")

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))
    if audience:
        qs = qs.filter(audience=audience)

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "notices/notice_list.html", {
        "page_obj": page_obj,
        "q": q,
        "audience": audience,
    })

def notice_detail(request, pk):
    notice = get_object_or_404(Notice, pk=pk)

    # 접근 제한: 비스태프는 published만
    if notice.status != "published" and not (request.user.is_authenticated and is_staff(request.user)):
        return redirect("notice_list")

    # 조회수 증가
    Notice.objects.filter(pk=pk).update(view_count=F("view_count") + 1)
    notice.refresh_from_db(fields=["view_count"])

    return render(request, "notices/notice_detail.html", {"notice": notice})

@user_passes_test(is_staff)
def notice_create(request):
    if request.method == "POST":
        form = NoticeForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.save()
            return redirect("notice_detail", pk=obj.pk)
    else:
        form = NoticeForm()
    return render(request, "notices/notice_form.html", {"form": form, "mode": "create"})

@user_passes_test(is_staff)
def notice_update(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    if request.method == "POST":
        form = NoticeForm(request.POST, request.FILES, instance=notice)
        if form.is_valid():
            form.save()
            return redirect("notice_detail", pk=pk)
    else:
        form = NoticeForm(instance=notice)
    return render(request, "notices/notice_form.html", {"form": form, "mode": "update", "notice": notice})

@user_passes_test(is_staff)
def notice_delete(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    if request.method == "POST":
        notice.delete()
        return redirect("notice_list")
    return render(request, "notices/notice_confirm_delete.html", {"notice": notice})
