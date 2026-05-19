from datetime import datetime
import json
from django.shortcuts import render
from django.urls import reverse

from .models import CollectedPost
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test

from .forms import SourceSiteForm
from django.core.paginator import Paginator

from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from django.shortcuts import render
from django.utils import timezone
from django.core.paginator import Paginator
from collections import defaultdict
import re

from collections import defaultdict
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils import timezone
from teachers.models import TeachingInstitution

from .constants import (
    DEPARTMENT_KEYWORD_MAP,
    DEPARTMENT_COLORS,
    DEPARTMENT_KEYWORDS,
)
from .models import CollectedPost, SourceSite
from schools.models import School
from .utils import highlight_department, normalize   # ✅ normalize 추가
from .utils import extract_program_keywords_from_title
from .utils import render_weekday_badges

from linkhub.models import NeulbomConfig
from django.db.models import Max


from datetime import datetime, date
from collections import defaultdict
from django.db.models import Max
from django.utils import timezone


SOURCE_COLOR_MAP = {

    # 🔹 전체
    "전체": "bg-dark",
    
    # 전남 공통
    "전남늘봄지원": "bg-success",

    # 전남 지역 교육지원청
    "영광교육지원청": "bg-orange",
    "나주교육지원청": "bg-info",
    "담양교육지원청": "bg-warning text-dark",
    "함평교육지원청": "bg-purple",
    "화순교육지원청": "bg-danger",
    "장성교육지원청": "bg-primary",
}

def post_hub(request):
    qs = CollectedPost.objects.select_related("source")

    # ===============================
    # 🔥 지역 페이지 분기
    # ===============================
    area = request.GET.get("area", "gwangju")

    if area == "gwangju":
        qs = qs.filter(region__startswith="광주")
        enable_department = True
    elif area == "jeonnam":
        qs = qs.filter(region__icontains="전라남도")
        enable_department = False
    else:
        enable_department = True

    # ===============================
    # 🔍 필터 파라미터
    # ===============================
    source_id = request.GET.get("source")
    status = request.GET.get("status")
    department = request.GET.get("department") if enable_department else None
    school_kw = request.GET.get("school", "").strip()

    if source_id:
        qs = qs.filter(source_id=source_id)

    posts = list(qs)
    today = timezone.localdate()

    # ===============================
    # 🔥 NEW / 상태 / 마감일 / 강조 계산
    # ===============================
    for p in posts:
        # NEW
        p.is_new_today = (p.collected_at.date() == today)

        # 상태
        p.auto_status = p.get_auto_status()

        p.source_badge_class = SOURCE_COLOR_MAP.get(
            p.source.name,
            "bg-secondary"
        )

         # 🔥 school_name 정제 (작성자 제거)
        if p.school_name:
            p.school_name = (
                p.school_name
                .replace("작성자", "")
                .replace(":", "")
                .strip()
            )


        # 모집 종료일 (정렬용) ✅ 안전 파싱 (지침)
        p.end_date = None
        if p.post_date:
            dates = re.findall(r"\d{2,4}[.\-]\d{1,2}[.\-]\d{1,2}", p.post_date)
            if len(dates) >= 2:
                try:
                    d = dates[1].replace(".", "-")
                    parts = d.split("-")

                    # 연도 없는 경우 → 올해 기준
                    if len(parts[0]) == 2:
                        year = date.today().year
                        month, day = map(int, parts)
                    else:
                        year, month, day = map(int, parts)

                    p.end_date = date(year, month, day)
                except Exception:
                    p.end_date = None


        # 우리 프로그램 여부
        p.is_our_program = False
        if p.school_name:
            matched_programs = extract_program_keywords_from_title(p.title)
            if matched_programs:
                p.is_our_program = TeachingInstitution.objects.filter(
                    place_type="school",
                    school__name=p.school_name,
                    program__in=matched_programs
                ).exists()

        # 제목 강조
        p.highlighted_title = highlight_department(
            p.title,
            department,
            DEPARTMENT_KEYWORD_MAP,
            DEPARTMENT_COLORS,
        )

        # 요일 badge
        p.weekday_badges = render_weekday_badges(p.weekday)

    # ===============================
    # 🔥 상태 필터
    # ===============================
    if status:
        posts = [p for p in posts if p.auto_status == status]

    # ===============================
    # 🔍 학교명 검색
    # ===============================
    if school_kw:
        kw_norm = normalize(school_kw)
        posts = [
            p for p in posts
            if kw_norm in normalize(p.school_name or "")
        ]

    # ===============================
    # 🔥 부서 필터
    # ===============================
    if department and department in DEPARTMENT_KEYWORD_MAP:
        keywords = DEPARTMENT_KEYWORD_MAP[department]
        posts = [
            p for p in posts
            if any(normalize(k) in normalize(p.title) for k in keywords)
        ]

    # ===============================
    # 🔥 정렬 (🔥 마감 빠른 순 핵심)
    # ===============================
    status_priority = {
        "마감임박": 0,
        "모집중": 1,
        "예정": 2,
        "마감": 3,
        "": 9,
    }

    posts.sort(
        key=lambda p: (
            status_priority.get(p.auto_status, 9),  # 상태
            p.end_date or date.max,                 # ✅ 마감일 빠른 순
            not p.is_new_today,                     # NEW 우선
            -p.collected_at.timestamp(),            # 최신 수집
        )
    )

    # ===============================
    # 🏫 학교별 그룹화 + NEW 여부
    # ===============================
    grouped = defaultdict(list)
    for p in posts:
        grouped[p.school_name or "학교명 없음"].append(p)

    grouped_posts = []

    for school_name, plist in grouped.items():
        student_count = "-"

        if school_name != "학교명 없음":
            school_obj = School.objects.filter(name=school_name).first()
            if school_obj and school_obj.student_count:
                student_count = school_obj.student_count

        grouped_posts.append({
            "school": school_name,
            "student_count": student_count,
            "posts": plist,
            "has_new": any(p.is_new_today for p in plist),  # ✅ 학교 NEW 표시
        })

    paginator = Paginator(grouped_posts, 100)
    page_obj = paginator.get_page(request.GET.get("page"))

    # ===============================
    # 🔥 늘봄 수집 기준일 / 최근 수집일
    # ===============================
    config = NeulbomConfig.objects.first()
    cutoff_date = config.cutoff_date if config else None

    latest_collected_at = CollectedPost.objects.aggregate(
        last=Max("collected_at")
    )["last"]

    latest_collected_date = (
        timezone.localtime(latest_collected_at).date()
        if latest_collected_at else None
    )

    # ===============================
    # 🔥 SourceSite 지역별 분리
    # ===============================
    if area == "jeonnam":
        sources = SourceSite.objects.filter(active=True, area="JEONNAM")
    else:
        sources = SourceSite.objects.filter(active=True)

    # 🔥 SourceSite 색상 매핑 (라디오 버튼용)
    for s in sources:
        s.badge_class = SOURCE_COLOR_MAP.get(
            s.name,
            "bg-secondary"
        )

    return render(request, "linkhub/post_hub.html", {
        "groups": page_obj,
        "page_obj": page_obj,
        "sources": sources, 
        "departments": DEPARTMENT_KEYWORDS,
        "enable_department": enable_department,
        "area": area,
        "selected": {
            "source": source_id,
            "status": status,
            "department": department,
            "school": school_kw,
        },
        "cutoff_date": cutoff_date,
        "latest_collected_date": latest_collected_date,
        "crontab_active": _crontab_is_active() if request.user.is_staff else False,
    })



def post_hub_gwangju(request):
    qs = CollectedPost.objects.select_related("source") \
        .filter(region__startswith="광주")

    return post_hub(
        request,
        qs,
        title="광주 늘봄 모집 공고",
        enable_department=True
    )

def post_hub_jeonnam(request):
    qs = CollectedPost.objects.select_related("source") \
        .filter(region__contains="전라남도")

    return post_hub(
        request,
        qs,
        title="전남 방과후 / 늘봄 모집 공고",
        enable_department=False
    )



from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.urls import reverse

from .models import CollectedPost


@staff_member_required
@require_POST
def collectedpost_delete_all(request):
    """
    모집/공지 통합 보기의 수집된 게시글 삭제
    - 지역(area) 기준으로만 삭제
    - staff만 가능, POST만 허용
    """

    area = request.POST.get("area", "gwangju")

    if area == "jeonnam":
        qs = CollectedPost.objects.filter(region__icontains="전라남도")
        area_label = "전남"
    else:
        qs = CollectedPost.objects.filter(region__startswith="광주")
        area_label = "광주"

    deleted_count = qs.count()
    qs.delete()

    messages.success(
        request,
        f"{area_label} 수집 데이터 {deleted_count}건을 삭제했습니다."
    )

    return redirect(f"{reverse('linkhub:post_hub')}?area={area}")


from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required

from .services import (
    collect_neulbom,
    collect_jne_common,
    collect_jne_region,
)


@staff_member_required
@require_POST
def collect_posts_view(request):
    area = request.POST.get("area", "gwangju")

    if area == "jeonnam":
        sites = SourceSite.objects.filter(active=True, area="JEONNAM")
    else:
        sites = SourceSite.objects.filter(active=True, area="GWANGJU")

    if not sites.exists():
        messages.error(request, "해당 지역에 활성화된 수집 사이트가 없습니다.")
        return redirect(f"{reverse('linkhub:post_hub')}?area={area}")

    # 🔥 기존 NEW 해제
    CollectedPost.objects.filter(is_new=True).update(is_new=False)

    total_new = 0

    for site in sites:
        try:
            if site.collector == "NEULBOM":
                new_count = collect_neulbom(site)
            elif site.collector == "JNE_COMMON":
                new_count = collect_jne_common(site)
            elif site.collector == "JNE_REGION":
                new_count = collect_jne_region(site)
            else:
                continue

            total_new += new_count

        except Exception as e:
            print(f"[수집 오류] {site.name}: {e}")

    messages.success(
        request,
        f"{'광주' if area=='gwangju' else '전남'} 수집 완료: 신규 공고 {total_new}건"
    )

    return redirect(f"{reverse('linkhub:post_hub')}?area={area}")



@staff_member_required
def source_list(request):
    area = request.GET.get("area", "gwangju")

    if area == "jeonnam":
        sources = SourceSite.objects.filter(area="JEONNAM")
    else:
        sources = SourceSite.objects.filter(area="GWANGJU")

    return render(request, "linkhub/source_list.html", {
        "sources": sources,
        "area": area,
    })



@staff_member_required
def source_create(request):
    area = request.GET.get("area", "gwangju")

    if request.method == "POST":
        form = SourceSiteForm(request.POST)
        if form.is_valid():
            source = form.save(commit=False)

            # 🔥 지역 자동 지정
            source.area = "JEONNAM" if area == "jeonnam" else "GWANGJU"
            source.save()

            messages.success(request, "SourceSite가 추가되었습니다.")
            return redirect(f"{reverse('linkhub:source_list')}?area={area}")
    else:
        form = SourceSiteForm()

    return render(request, "linkhub/source_form.html", {
        "form": form,
        "mode": "add",
        "area": area,
    })



@staff_member_required
def source_update(request, pk):
    source = get_object_or_404(SourceSite, pk=pk)
    area = source.area.lower()  # GWANGJU → gwangju

    if request.method == "POST":
        form = SourceSiteForm(request.POST, instance=source)
        if form.is_valid():
            form.save()
            messages.success(request, "SourceSite가 수정되었습니다.")
            return redirect(f"{reverse('linkhub:source_list')}?area={area}")
    else:
        form = SourceSiteForm(instance=source)

    return render(request, "linkhub/source_form.html", {
        "form": form,
        "mode": "edit",
        "area": area,
    })



@staff_member_required
def source_delete(request, pk):
    source = get_object_or_404(SourceSite, pk=pk)
    area = source.area.lower()

    if request.method == "POST":
        source.delete()
        messages.success(request, "SourceSite가 삭제되었습니다.")
        return redirect(f"{reverse('linkhub:source_list')}?area={area}")

    return render(request, "linkhub/source_confirm_delete.html", {
        "source": source,
        "area": area,
    })


@require_POST
@user_passes_test(lambda u: u.is_staff)
def source_toggle_active(request, pk):
    site = SourceSite.objects.get(pk=pk)
    site.active = not site.active
    site.save(update_fields=["active"])

    return JsonResponse({
        "active": site.active
    })


@csrf_exempt
@require_POST
def collect_receive_api(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "invalid json"}, status=400)

    saved = 0
    received = len(payload)

    for item in payload:
        source = SourceSite.objects.get(id=item["source_id"])

        _, created = CollectedPost.objects.get_or_create(
            source=source,
            mng_no=item["mng_no"],
            defaults={
                "title": item["title"],
                "link": item["link"],
                "region": item.get("region", ""),
                "school_name": item.get("school_name", ""),
                "post_date": item.get("post_date", ""),
                "status": item.get("status", ""),
                "is_new": True,
            }
        )
        if created:
            saved += 1

    return JsonResponse({"ok": True, "received": received, "saved": saved})

# linkhub/views.py
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json
from .models import NeulbomConfig
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
@require_POST
def neulbom_cutoff_update(request):
    try:
        payload = json.loads(request.body)
        cutoff_date = payload.get("cutoff_date")
    except Exception:
        return JsonResponse({"ok": False}, status=400)

    config, _ = NeulbomConfig.objects.get_or_create(
        id=1,
        defaults={"cutoff_date": cutoff_date}
    )
    config.cutoff_date = cutoff_date
    config.save(update_fields=["cutoff_date"])

    return JsonResponse({
        "ok": True,
        "cutoff_date": cutoff_date
    })


import subprocess
import sys
from django.conf import settings

def _crontab_is_active():
    """현재 crontab에 collect_linkhub 등록 여부 확인"""
    try:
        result = subprocess.run(
            [sys.executable, "manage.py", "crontab", "show"],
            capture_output=True, text=True, cwd=settings.BASE_DIR
        )
        return "collect_linkhub" in result.stdout
    except Exception:
        return False


@staff_member_required
@require_POST
def crontab_toggle(request):
    currently_active = _crontab_is_active()
    action = "remove" if currently_active else "add"
    try:
        subprocess.run(
            [sys.executable, "manage.py", "crontab", action],
            capture_output=True, text=True, cwd=settings.BASE_DIR, timeout=15
        )
        new_state = not currently_active
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

    return JsonResponse({"ok": True, "active": new_state})
