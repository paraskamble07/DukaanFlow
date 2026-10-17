from decimal import Decimal
import urllib.parse
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Q
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


def normalize_phone_number(raw):
    """Normalize a phone string to bare digits.

    Strips spaces, dashes, brackets and a leading +; a 12-digit number
    starting with 91 (the India country code) collapses to the 10-digit
    national number, so 98765 43210, +91-9876543210 and 09876543210 all
    compare as 9876543210.
    """
    if raw is None:
        return ''
    digits = ''.join(ch for ch in str(raw) if ch.isdigit())
    if len(digits) == 12 and digits.startswith('91'):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith('0'):
        digits = digits[1:]
    return digits


# Numbers a user types when the customer's real number is unknown. Several
# such customers (e.g. walk-in ledgers) may coexist in one shop, so the
# per-phone unique constraint and the dedup check both skip them.
PLACEHOLDER_PHONES = (
    '0000000000', '1111111111', '2222222222', '3333333333', '4444444444',
    '5555555555', '6666666666', '7777777777', '8888888888', '9999999999',
    '1234567890',
)


def customer_duplicate_key(raw):
    """The key two customers of one shop must never share, or None.

    None means "do not deduplicate": short numbers and obvious placeholders
    (all-same-digit strings, 1234567890) are what users type when they do
    not know a customer's real number — several such customers (e.g. a
    walk-in ledger) must stay separable.
    """
    digits = normalize_phone_number(raw)
    if len(digits) < 10:
        return None
    key = digits[-10:]
    if key in PLACEHOLDER_PHONES:
        return None
    return key


def find_duplicate_customer(business, raw_phone, exclude_id=None):
    """Return the existing customer of `business` sharing the phone key, if any."""
    from customers.models import Customer
    key = customer_duplicate_key(raw_phone)
    if not key:
        return None
    qs = Customer.objects.filter(business=business)
    if exclude_id is not None:
        qs = qs.exclude(pk=exclude_id)
    # Stored numbers are normalized on save; match bare, 0- or 91-prefixed
    # spellings so pre-normalization rows are caught too.
    for customer in qs.filter(Q(phone=key) | Q(phone__endswith=key)):
        if customer_duplicate_key(customer.phone) == key:
            return customer
    return None


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
