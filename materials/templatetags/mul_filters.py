# === 파일: materials/templatetags/mul_filters.py ===
from django import template
register = template.Library()

@register.filter
def mul(value, arg):
    """value × arg 곱하기 필터"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return ''
