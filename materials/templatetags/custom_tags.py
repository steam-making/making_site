from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    """딕셔너리에서 key로 값 가져오기"""
    return dictionary.get(key)
