# myapp/templatetags/math_filters.py
from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """
    คูณ value กับ arg แล้วคืนค่ากลับ
    Usage: {{ value|mul:arg }}
    """
    try:
        return value * arg
    except Exception:
        return ''

