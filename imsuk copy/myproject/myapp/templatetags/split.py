# myapp/templatetags/split.py
from django import template

register = template.Library()

@register.filter
def split(value, sep):
    return [v.strip() for v in value.split(sep)]
