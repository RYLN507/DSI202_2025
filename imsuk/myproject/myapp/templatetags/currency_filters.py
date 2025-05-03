# myapp/templatetags/currency_filters.py
from django import template

register = template.Library()

@register.filter
def currency(value, symbol='฿'):
    """
    แปลงตัวเลขให้มีคอมม่าเป็นหลักหมื่น และเติม symbol ข้างหน้า
    Usage: {{ value|currency:"฿" }}
    """
    try:
        # แปลงให้เป็น float ก่อน แล้วจัด format ให้มี comma
        val = float(value)
    except (TypeError, ValueError):
        return value
    # ไม่มีทศนิยม
    formatted = f"{val:,.0f}"
    return f"{symbol}{formatted}"