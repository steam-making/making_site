from django import template
from recruit.program_colors import PROGRAM_COLORS

register = template.Library()

@register.filter
def program_color(program_name):
    return PROGRAM_COLORS.get(program_name, "secondary")
