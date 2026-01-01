from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """곱셈 필터"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def dict_get(d, key):
    """딕셔너리 값 가져오기"""
    try:
        return d.get(str(key)) if d else None
    except Exception:
        return None

@register.filter(name='add_class')
def add_class(field, css_class):
    """폼 필드에 동적으로 CSS 클래스를 추가"""
    return field.as_widget(attrs={"class": css_class})
