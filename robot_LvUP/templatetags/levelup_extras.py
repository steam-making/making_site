from django import template

register = template.Library()

@register.filter
def percent_of(value, total):
    """비율(%) 계산"""
    try:
        return round((int(value) / int(total)) * 100, 1)
    except (ZeroDivisionError, ValueError, TypeError):
        return 0

@register.filter
def progress_color(value, total):
    """진행률에 따른 색상 클래스 반환"""
    try:
        percent = (int(value) / int(total)) * 100
        if percent >= 80:
            return "high"
        elif percent >= 50:
            return "mid"
        else:
            return "low"
    except (ZeroDivisionError, ValueError, TypeError):
        return "low"
    
from django import template

register = template.Library()

@register.filter
def dict_get(d, key):
    if isinstance(d, dict):
        return d.get(key)
    return None

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
