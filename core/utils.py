from decimal import Decimal
import urllib.parse
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def format_inr(val):
    if val is None:
        return "₹0.00"
    try:
        d = Decimal(str(val))
    except Exception:
        return f"₹{val}"
    is_neg = d < 0
    d = abs(d)
    parts = f"{d:.2f}".split('.')
    int_part = parts[0]
    dec_part = parts[1]
    if len(int_part) <= 3:
        formatted_int = int_part
    else:
        last3 = int_part[-3:]
        rem = int_part[:-3]
        groups = []
        while len(rem) > 2:
            groups.insert(0, rem[-2:])
            rem = rem[:-2]
        if rem:
            groups.insert(0, rem)
        formatted_int = ",".join(groups) + "," + last3
    return f"{'-' if is_neg else ''}₹{formatted_int}.{dec_part}"

def build_whatsapp_url(phone, message):
    if not phone:
        return ""
    # Clean phone to 10-12 digits, prepend 91 if 10 digits
    clean_phone = "".join(ch for ch in str(phone) if ch.isdigit())
    if len(clean_phone) == 10:
        clean_phone = "91" + clean_phone
    encoded_msg = urllib.parse.quote(message)
    return f"https://wa.me/{clean_phone}?text={encoded_msg}"

def business_required(view_func):
    """Decorator that ensures user is logged in and has an active business."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not getattr(request, 'business', None):
            messages.warning(request, "Please set up your business details first to continue.")
            return redirect('businesses:onboarding')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
