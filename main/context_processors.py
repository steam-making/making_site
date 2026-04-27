from .models import MenuItem

def menu_items(request):
    user = request.user
    
    # 기본적으로 활성화 상태인 것만 가져오고 sub_menus를 prefetch하여 쿼리 효율 최적화
    all_menus = MenuItem.objects.filter(is_active=True).prefetch_related('sub_menus')
    
    # 필터링 로직: 현재 로그인한 사용자의 권한에 맞는 메뉴만 취합
    allowed_menus = []
    
    for menu in all_menus:
        show = False
        al = menu.access_level
        
        # 1순위: 관리자는 설정과 관계없이 모든 활성 메뉴를 다 볼 수 있음
        if user.is_staff:
            show = True
        # 2순위: 비로그인 또는 일반 권한 체크
        elif al == 'all':
            show = True
        elif user.is_authenticated:
            user_type = getattr(getattr(user, 'profile', None), 'user_type', None)
            if al == 'teacher' and user_type in ('teacher', 'center_teacher'):
                show = True
            elif al == 'institution' and user_type == 'institution':
                show = True
        
        if show:
            allowed_menus.append(menu)

    # 트리 구조 생성 (최상위 메뉴만 반환, 하위 메뉴는 prefetch됨)
    top_menus = [m for m in allowed_menus if m.parent is None]
    
    return {
        'global_menu': top_menus
    }
