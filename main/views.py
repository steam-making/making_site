from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Max
from django.http import JsonResponse
from teachers.models import TeachingInstitution
from .models import MenuItem

def home(request):
    institutions = TeachingInstitution.objects.all().order_by('-id')[:6]
    return render(request, 'main/home.html', {
        'institutions': institutions
    })

def making_page(request):
    return render(request, 'main/making.html')

@staff_member_required
def menu_management(request):
    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == "delete":
            menu_id = request.POST.get('menu_id')
            MenuItem.objects.filter(id=menu_id).delete()
            messages.success(request, "메뉴가 삭제되었습니다.")
            return redirect('menu_management')
        
        elif action == "update":
            menu_id = request.POST.get('menu_id')
            parent_id = request.POST.get('parent_id')
            parent = get_object_or_404(MenuItem, id=parent_id) if parent_id else None
            
            if menu_id:
                menu = get_object_or_404(MenuItem, id=menu_id)
            else:
                menu = MenuItem()
                max_order = MenuItem.objects.filter(parent=parent).aggregate(Max('order'))['order__max'] or 0
                menu.order = max_order + 1
                
            menu.title = request.POST.get('title')
            menu.url = request.POST.get('url')
            menu.icon_class = request.POST.get('icon_class', '')
            menu.access_level = request.POST.get('access_level', 'all')
            menu.is_active = request.POST.get('is_active') == 'on'
            menu.parent = parent
            menu.save()
            messages.success(request, "메뉴 정보가 저장되었습니다.")
            return redirect('menu_management')

        elif action == "save_order":
            # 드래그 앤 드롭 후 전체 순서 저장
            ordered_ids = request.POST.getlist('order[]')
            for index, menu_id in enumerate(ordered_ids):
                MenuItem.objects.filter(id=menu_id).update(order=index + 1)
            return JsonResponse({'status': 'success'})

    top_menus = MenuItem.objects.filter(parent=None).order_by('order')
    return render(request, 'main/menu_management.html', {
        'top_menus': top_menus,
        'access_choices': MenuItem.ACCESS_LEVELS
    })