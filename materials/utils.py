from django.urls import reverse
from django.http import HttpResponseRedirect

def redirect_with_filters(request, view_name, *args, **kwargs):
    """
    release_list 같은 목록 뷰로 redirect 할 때
    현재 GET 파라미터(teacher, institution, order_month)를 그대로 유지해서 돌려보낸다.
    """
    url = reverse(view_name, args=args, kwargs=kwargs)
    query = request.GET.urlencode()
    if query:
        url = f"{url}?{query}"
    return HttpResponseRedirect(url)


from .models import MaterialHistory

def log_material_history(material, user, change_type, old_value, new_value, note=""):
    MaterialHistory.objects.create(
        material=material,
        user=user,
        change_type=change_type,
        old_value=old_value,
        new_value=new_value,
        note=note,
    )