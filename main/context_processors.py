from .models import MenuItem


def _can_access_menu(user, menu):
    if user.is_staff:
        return True

    if menu.access_level == 'all':
        return True

    if not user.is_authenticated:
        return False

    user_type = getattr(getattr(user, 'profile', None), 'user_type', None)
    if menu.access_level == 'teacher' and user_type in ('teacher', 'center_teacher'):
        return True
    if menu.access_level == 'institution' and user_type == 'institution':
        return True

    return False


def menu_items(request):
    user = request.user

    # 기본적으로 활성화 상태인 것만 가져오고 sub_menus를 prefetch하여 쿼리 효율 최적화
    all_menus = list(MenuItem.objects.filter(is_active=True).prefetch_related('sub_menus'))
    allowed_ids = {menu.id for menu in all_menus if _can_access_menu(user, menu)}

    top_menus = []
    for menu in all_menus:
        if menu.parent_id is not None or menu.id not in allowed_ids:
            continue

        visible_sub_menus = [sub for sub in menu.sub_menus.all() if sub.is_active and sub.id in allowed_ids]
        menu.visible_sub_menus = visible_sub_menus

        # 하위 메뉴형 그룹은 실제로 보여줄 항목이 있을 때만 노출
        if visible_sub_menus or menu.url != '#':
            top_menus.append(menu)

    # 새 linkhub 공고 수 (영역별) - 오늘 수집된 것 기준
    try:
        from linkhub.models import CollectedPost
        from django.utils import timezone
        today = timezone.localdate()
        new_qs = CollectedPost.objects.filter(
            collected_at__date=today
        ).values_list('source__area', flat=True)
        areas = list(new_qs)
        linkhub_new_gwangju = areas.count('GWANGJU')
        linkhub_new_jeonnam = areas.count('JEONNAM')
    except Exception:
        linkhub_new_gwangju = 0
        linkhub_new_jeonnam = 0

    return {
        'global_menu': top_menus,
        'linkhub_new_gwangju': linkhub_new_gwangju,
        'linkhub_new_jeonnam': linkhub_new_jeonnam,
    }
