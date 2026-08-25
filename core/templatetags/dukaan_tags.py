from django import template
from decimal import Decimal
import urllib.parse

register = template.Library()

@register.filter
def inr(value):
    """Formats a decimal or float into Indian Rupee format: ₹1,25,000.00"""
    if value is None or value == '':
        return "₹0.00"
    try:
        val = Decimal(str(value))
    except Exception:
        return f"₹{value}"
    
    is_neg = val < 0
    val = abs(val)
    
    # Split integer and decimal parts
    parts = f"{val:.2f}".split('.')
    int_part = parts[0]
    dec_part = parts[1]
    
    if len(int_part) <= 3:
        formatted_int = int_part
    else:
        last3 = int_part[-3:]
        remaining = int_part[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted_int = ",".join(groups) + "," + last3
        
    prefix = "-₹" if is_neg else "₹"
    return f"{prefix}{formatted_int}.{dec_part}"

@register.filter
def urlencode_text(value):
    if not value:
        return ""
    return urllib.parse.quote(str(value))

@register.filter
def multiply(value, arg):
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except Exception:
        return 0

@register.filter
def subtract(value, arg):
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except Exception:
        return 0
