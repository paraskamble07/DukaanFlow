from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import HasActiveBusiness, CustomersPermission
from core.utils import build_whatsapp_url, format_inr
from customers.models import Customer
from sales.models import Sale
from payments.models import Payment

from .models import ReminderLog, ReminderSetting

# A reminder per (customer, channel) cannot be logged more often than
# this, which prevents accidental double-taps from spamming a customer.
REMINDER_COOLDOWN = timedelta(hours=1)


def get_settings(business):
    setting, _ = ReminderSetting.objects.get_or_create(business=business)
    return setting


def derive_due_date(customer, credit_days):
    """Due date comes from the OLDEST still-unpaid credit sale, so a
    customer who keeps adding khata bills is reminded about the aging
    balance. Falls back to the latest sale when needed."""
    sales = Sale.objects.filter(
        business=customer.business, customer=customer,
    ).order_by('sale_date')
    for sale in sales:
        if sale.due_amount > 0:
            return (sale.sale_date.date() if sale.sale_date else sale.created_at.date()) + timedelta(days=credit_days)
    latest = sales.first()
    if latest is None:
        return None
    return (latest.sale_date.date() if latest.sale_date else latest.created_at.date()) + timedelta(days=credit_days)


def reminder_message(customer, business, due, due_date):
    """Payment reminder body: shop identity (name, address, phone) plus
    the customer, due date and outstanding balance."""
    shop_name = business.name or 'our shop'
    address = ', '.join(
        str(x) for x in (business.address, business.city, business.state, business.pincode)
        if x
    ) or None
    phone = business.phone or None
    lines = [
        f'Namaste {customer.name},',
        '',
        f'This is a friendly payment reminder from {shop_name}.',
        f'Your outstanding Khata balance is *{format_inr(due)}*.',
    ]
    if due_date is not None:
        lines.append(f'Payment was due on *{due_date:%d-%m-%Y *}as per your credit bill.')
    lines.append('')
    if address or phone:
        lines.append('Visit or contact us:')
        if address:
            lines.append(address)
        if phone:
            lines.append(f'Phone: {phone}')
        lines.append('')
    lines.append('Please settle the payment at your earliest convenience. Thank you!')
    return '\n'.join(lines)


def sms_body(customer, business, due, due_date):
    """SMS composer body — compact plain text."""
    base = f'{customer.name}: {format_inr(due)} pending with {business.name or "our shop"}'
    if due_date is not None:
        base += f' (due {due_date:%d-%m-%Y})'
    contact = business.phone or ''
    if contact:
        base += f'. Contact {contact}'
    return base + '. Pay soon. Thank you!'


class DueListAPIView(APIView):
    """Authoritative list of customers with an outstanding balance,
    their derived due date, status and recent reminder history.
    Settled balances are excluded."""

    permission_classes = [IsAuthenticated, HasActiveBusiness, CustomersPermission]

    def get(self, request):
        business = request.business
        setting = get_settings(business)
        today = timezone.now().date()
        due_soon_window = setting.due_soon_days or 7

        customers = Customer.objects.filter(business=business)
        result = []
        for customer in customers:
            due = customer.get_outstanding_due()
            if due <= 0:
                continue  # Settled (or never credited) — cannot be reminded.

            due_date = derive_due_date(customer, setting.credit_days)
            if due_date is None:
                st = 'DUE'
            elif due_date < today:
                st = 'OVERDUE'
            elif (due_date - today).days <= due_soon_window:
                st = 'DUE_SOON'
            else:
                st = 'DUE'

            recent = ReminderLog.objects.filter(customer=customer)[:3]
            result.append({
                'customer_id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'outstanding': str(due),
                'due_date': due_date.isoformat() if due_date else None,
                'status': st,
                'last_reminder': {
                    'channel': log.channel,
                    'at': log.created_at.isoformat(),
                } if recent else None,
                'reminder_count': ReminderLog.objects.filter(customer=customer).count(),
                'whatsapp_url': build_whatsapp_url(
                    customer.phone, reminder_message(customer, business, due, due_date)),
                'sms_body': sms_body(customer, business, due, due_date),
            })

        result.sort(key=lambda r: (r['status'] != 'OVERDUE', r['status'] != 'DUE_SOON',
                                   r['reminder_count'], r['name']))
        return Response({
            'today': today.isoformat(),
            'credit_days': setting.credit_days,
            'due_soon_days': due_soon_window,
            'results': result,
            'count': len(result),
        })


class ReminderLogCreateAPIView(APIView):
    """Log a user-confirmed reminder (composer action). The server
    recalculates the outstanding balance before accepting and rejects
    settled balances; a duplicate within the cooldown is rejected."""

    permission_classes = [IsAuthenticated, HasActiveBusiness, CustomersPermission]

    def post(self, request):
        customer_id = request.data.get('customer_id')
        channel = (request.data.get('channel') or '').upper()
        note = (request.data.get('note') or '').strip()

        if not customer_id:
            return Response({'error': 'customer_id is required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if channel not in ('WHATSAPP', 'SMS', 'OTHER'):
            return Response({'error': 'channel must be WHATSAPP, SMS or OTHER.'},
                            status=status.HTTP_400_BAD_REQUEST)

        customer = Customer.objects.filter(id=customer_id, business=request.business).first()
        if customer is None:
            return Response({'error': 'Customer not found.'},
                            status=status.HTTP_404_NOT_FOUND)

        # Re-read the authoritative balance — never trust the client.
        due = customer.get_outstanding_due()
        if due <= 0:
            return Response({'error': 'This customer has no outstanding balance; nothing to remind.'},
                            status=status.HTTP_400_BAD_REQUEST)

        recent = ReminderLog.objects.filter(
            customer=customer, channel=channel,
            created_at__gte=timezone.now() - REMINDER_COOLDOWN,
        ).first()
        if recent is not None:
            return Response({
                'error': f'A {channel} reminder was already logged for this customer recently. Please wait before sending another.',
                'last_at': recent.created_at.isoformat(),
            }, status=status.HTTP_409_CONFLICT)

        setting = get_settings(request.business)
        due_date = derive_due_date(customer, setting.credit_days)
        today = timezone.now().date()
        if due_date and due_date < today:
            rem_status = 'OVERDUE'
        elif due_date and (due_date - today).days <= (setting.due_soon_days or 7):
            rem_status = 'DUE_SOON'
        else:
            rem_status = 'DUE'

        # The credit sale this reminder refers to (oldest unpaid bill).
        sale = Sale.objects.filter(
            business=request.business, customer=customer, due_amount__gt=0,
        ).order_by('sale_date').first()

        with transaction.atomic():
            log = ReminderLog.objects.create(
                business=request.business,
                customer=customer,
                sale=sale,
                amount=due,
                due_date=due_date,
                channel=channel,
                reminder_status=rem_status,
                note=note,
                sent_by=request.user,
            )

        return Response({
            'id': log.id,
            'message': 'Reminder logged. The share sheet opened on your phone confirms delivery — this app never sends messages silently.',
            'amount': str(log.amount),
            'due_date': due_date.isoformat() if due_date else None,
            'channel': log.channel,
        }, status=status.HTTP_201_CREATED)


class ReminderHistoryAPIView(APIView):
    """Reminder history for the shop (optionally filtered by customer)."""

    permission_classes = [IsAuthenticated, HasActiveBusiness, CustomersPermission]

    def get(self, request):
        qs = ReminderLog.objects.filter(business=request.business).order_by('-created_at')
        customer_id = request.query_params.get('customer_id')
        if customer_id:
            qs = qs.filter(customer_id=customer_id)

        results = []
        for log in qs[:100]:
            results.append({
                'id': log.id,
                'customer': log.customer.name,
                'customer_id': log.customer_id,
                'amount': str(log.amount),
                'due_date': log.due_date.isoformat() if log.due_date else None,
                'channel': log.channel,
                'status': log.reminder_status,
                'note': log.note,
                'sent_at': log.created_at.isoformat(),
                'sent_by': (log.sent_by.get_full_name() or log.sent_by.email) if log.sent_by else None,
            })
        total = ReminderLog.objects.filter(business=request.business).count()
        return Response({'results': results, 'count': total})
