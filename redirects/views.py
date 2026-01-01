import qrcode
import io
from django.http import HttpResponse
from .models import DynamicLink
from PIL import Image
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q, F
from .forms import DynamicLinkForm

def dynamic_redirect(request, key):
    """key에 해당하는 최종 URL로 리디렉션"""
    link = get_object_or_404(DynamicLink, key=key)
    return redirect(link.url)

def qr_code(request, key):
    """key에 해당하는 QR 코드 PNG 생성 (오른쪽 하단 로고 포함)"""
    link = get_object_or_404(DynamicLink, key=key)
    qr_url = request.build_absolute_uri(f"/q/{link.key}/")

    # QR 코드 생성
    qr = qrcode.QRCode(
        version=3,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)

    img_qr = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # 로고 삽입
    try:
        logo = Image.open("static/images/making_logo(500px).png")  # 🔹 로고 경로 수정 가능
        # 로고 크기 조정 (QR 폭의 15% 정도)
        qr_width, qr_height = img_qr.size
        logo_size = qr_width // 6
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

        # 오른쪽 하단 위치 계산 (여백 조금 두기)
        pos = (qr_width - logo_size - 40, qr_height - logo_size - 40)
        img_qr.paste(logo, pos, mask=logo if logo.mode == "RGBA" else None)
    except FileNotFoundError:
        pass

    buffer = io.BytesIO()
    img_qr.save(buffer, format="PNG")
    buffer.seek(0)

    return HttpResponse(buffer, content_type="image/png")

# ✅ 목록
@staff_member_required
def link_list(request):
    q = request.GET.get("q", "")
    only_active = request.GET.get("active") == "1"
    links = DynamicLink.objects.all()
    if q:
        links = links.filter(Q(key__icontains=q) | Q(url__icontains=q) | Q(title__icontains=q))
    if only_active:
        links = links.filter(is_active=True)
    return render(request, "redirects/link_list.html", {"links": links, "q": q, "only_active": only_active})

# ✅ 추가
@staff_member_required
def link_create(request):
    if request.method == "POST":
        form = DynamicLinkForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "링크가 추가되었습니다.")
            return redirect("redirects:link_list")
    else:
        form = DynamicLinkForm()
    return render(request, "redirects/link_form.html", {"form": form, "mode": "create"})

# ✅ 수정
@staff_member_required
def link_update(request, pk):
    link = get_object_or_404(DynamicLink, pk=pk)
    if request.method == "POST":
        form = DynamicLinkForm(request.POST, instance=link)
        if form.is_valid():
            form.save()
            messages.success(request, "수정되었습니다.")
            return redirect("redirects:link_list")
    else:
        form = DynamicLinkForm(instance=link)
    return render(request, "redirects/link_form.html", {"form": form, "mode": "update", "link": link})

# ✅ 삭제
@staff_member_required
def link_delete(request, pk):
    link = get_object_or_404(DynamicLink, pk=pk)
    if request.method == "POST":
        link.delete()
        messages.success(request, "삭제되었습니다.")
        return redirect("redirects:link_list")
    return render(request, "redirects/link_confirm_delete.html", {"link": link})

# ✅ QR 다운로드
@staff_member_required
def qr_download(request, key):
    """QR PNG 파일 다운로드"""
    response = qr_code(request, key)
    response["Content-Disposition"] = f'attachment; filename="{key}.png"'
    return response