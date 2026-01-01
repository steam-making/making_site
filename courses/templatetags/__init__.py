from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    dictionary[key] 형태로 값 가져오는 필터
    템플릿에서 progress|get_item:chapter.id 로 사용
    """
    try:
        return dictionary.get(key, 0)
    except:
        return 0
