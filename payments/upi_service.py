"""UPI collect-QR helpers (Phase 6).

Design rule from the master prompt: scanning a QR is **not** a payment.
These helpers only build a collect request (the `upi://pay?...` URI and its
QR image). A payment enters the books solely when an authorized shop user
records it via the payment API, which validates the amount server-side.
"""
import base64
import io
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

import qrcode

ZERO = Decimal('0.00')


def parse_money(raw):
    """Strict, float-free money parser. Returns None when not a valid amount."""
    if raw is None:
        return None
    try:
        amount = Decimal(str(raw).strip())
    except (InvalidOperation, ValueError, TypeError):
        return None
    if amount <= 0:
        return None
    return amount.quantize(Decimal('0.01'))


def build_upi_uri(upi_id, payee_name, amount=None, note=None):
    """Build a `upi://pay?...` collect URI (NPCI's common UPI deep link)."""
    uri = 'upi://pay?pa=%s&pn=%s' % (quote(str(upi_id).strip()), quote(str(payee_name).strip()))
    if amount is not None and amount > 0:
        uri += '&am=%s&cu=INR' % str(amount.quantize(Decimal('0.01')))
    if note:
        uri += '&tn=%s' % quote(str(note))
    return uri


def upi_qr_png_base64(uri, box_size=10, border=2):
    """Render `uri` as a QR PNG and return it base64-encoded for JSON."""
    img = qrcode.make(uri, box_size=box_size, border=border)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('ascii')


def clean_upi_id(raw):
    """Normalize a configured UPI ID to a bare string, or None."""
    if raw is None:
        return None
    value = str(raw).strip()
    return value or None
