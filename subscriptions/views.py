from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import HasActiveBusiness
from businesses.models import Business, SHOPZEN_PREMIUM_PRICE
from .models import SubscriptionPaymentRequest, AdminAuditLog
from .permissions import IsShopZenAdmin


def _payment_config():
    """Configurable payment settings — env-driven, nothing hard-coded."""
    return {
        'price': SHOPZEN_PREMIUM_PRICE,
        'price_display': f'₹{SHOPZEN_PREMIUM_PRICE}/month',
        'duration_days': 30,
        'upi_id': getattr(settings, 'SHOPZEN_UPI_ID', ''),
        'payee_name': getattr(settings, 'SHOPZEN_PAYEE_NAME', 'Paras Kamble'),
        'qr_image_url': getattr(settings, 'SHOPZEN_QR_IMAGE_URL', ''),
    }


class PaymentConfigAPIView(APIView):
    """Public payment config for the Premium screen (QR URL + UPI id + price)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cfg = _payment_config()
        return Response({
            'price': cfg['price'],
            'price_display': cfg['price_display'],
            'duration_days': cfg['duration_days'],
            'upi_id': cfg['upi_id'],
            'payee_name': cfg['payee_name'],
            'qr_image_url': cfg['qr_image_url'],
            'upi_intent_url': (
                f'upi://pay?pa={cfg["upi_id"]}&pn={cfg["payee_name"]}&am={cfg["price"]}&cu=INR'
                if cfg['upi_id'] else ''
            ),
        })


class MySubscriptionRequestsAPIView(APIView):
    """Shop owner: list own payment requests + current subscription status."""
    permission_classes = [IsAuthenticated, HasActiveBusiness]

    def get(self, request):
        business = request.business
        requests_qs = SubscriptionPaymentRequest.objects.filter(business=business)[:10]
        return Response({
            'subscription': {
                'is_active': business.is_subscription_active(),
                'start_date': business.subscription_start_date.strftime('%d-%m-%Y'),
                'end_date': business.subscription_end_date.strftime('%d-%m-%Y'),
                'days_remaining': business.days_until_expiry(),
            },
            'pending_request': bool(SubscriptionPaymentRequest.objects.filter(
                business=business, status='PENDING').exists()),
            'requests': [{
                'id': r.id,
                'amount': str(r.amount),
                'upi_reference': r.upi_reference,
                'status': r.status,
                'created_at': r.created_at.strftime('%d-%m-%Y %H:%M'),
                'rejection_reason': r.rejection_reason,
            } for r in requests_qs],
        })


class SubmitPaymentRequestAPIView(APIView):
    """Shop owner: claim a ₹30 UPI payment. Creates a PENDING request only —
    Premium is NEVER activated here."""
    permission_classes = [IsAuthenticated, HasActiveBusiness]

    def post(self, request):
        business = request.business
        if SubscriptionPaymentRequest.objects.filter(business=business, status='PENDING').exists():
            return Response(
                {'error': 'You already have a payment request awaiting verification.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        amount = request.data.get('amount', SHOPZEN_PREMIUM_PRICE)
        try:
            amount = Decimal(str(amount))
        except Exception:
            return Response({'error': 'Invalid amount.'}, status=status.HTTP_400_BAD_REQUEST)
        if amount < Decimal('1'):
            return Response({'error': 'Invalid amount.'}, status=status.HTTP_400_BAD_REQUEST)

        obj = SubscriptionPaymentRequest.objects.create(
            business=business,
            requested_by=request.user,
            amount=amount,
            upi_reference=str(request.data.get('upi_reference', '')).strip()[:50],
            note=str(request.data.get('note', '')).strip(),
        )
        return Response({
            'message': 'Payment submitted successfully. Your subscription is waiting for verification.',
            'request_id': obj.id,
            'status': 'PENDING',
        }, status=status.HTTP_201_CREATED)


def _audit(admin, action, target, detail='', result='OK'):
    AdminAuditLog.objects.create(
        admin=admin, action=action, target=target, detail=detail, result=result
    )


class AdminDashboardAPIView(APIView):
    """ShopZen admin: platform-wide totals (no per-shop private data)."""
    permission_classes = [IsAuthenticated, IsShopZenAdmin]

    def get(self, request):
        from django.contrib.auth.models import User
        total_users = User.objects.filter(is_active=True).count()
        total_shops = Business.objects.count()
        active_subs = sum(1 for b in Business.objects.all() if b.is_subscription_active())
        requests_qs = SubscriptionPaymentRequest.objects.all()
        pending = requests_qs.filter(status='PENDING')
        from django.db.models import Sum
        revenue = requests_qs.filter(status='APPROVED').aggregate(
            total=Sum('amount'))['total'] or Decimal('0.00')
        recent_requests = requests_qs[:15]
        recent_regs = Business.objects.order_by('-id')[:10]
        return Response({
            'total_users': total_users,
            'total_shops': total_shops,
            'active_subscriptions': active_subs,
            'expired_subscriptions': total_shops - active_subs,
            'pending_payment_requests': pending.count(),
            'approved_payments': requests_qs.filter(status='APPROVED').count(),
            'rejected_payments': requests_qs.filter(status='REJECTED').count(),
            'total_subscription_revenue': str(revenue),
            'recent_registrations': [{
                'shop': b.name, 'owner': b.owner_name, 'email': b.owner.email,
                'created': b.subscription_start_date.strftime('%d-%m-%Y'),
            } for b in recent_regs],
            'recent_payment_requests': [{
                'id': r.id, 'shop': r.business.name, 'owner': r.business.owner_name,
                'email': r.requested_by.email, 'amount': str(r.amount),
                'upi_reference': r.upi_reference, 'status': r.status,
                'created_at': r.created_at.strftime('%d-%m-%Y %H:%M'),
            } for r in recent_requests],
            'system': {
                'time': timezone.localtime().strftime('%d-%m-%Y %H:%M'),
                'django_ok': True,
            },
        })


class AdminPaymentRequestsAPIView(APIView):
    """ShopZen admin: list/search payment requests."""
    permission_classes = [IsAuthenticated, IsShopZenAdmin]

    def get(self, request):
        qs = SubscriptionPaymentRequest.objects.select_related('business', 'requested_by')
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        q = request.query_params.get('q', '').strip()
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(business__name__icontains=q) | Q(upi_reference__icontains=q)
                | Q(requested_by__email__icontains=q)
            )
        return Response({'requests': [{
            'id': r.id, 'shop': r.business.name, 'owner': r.business.owner_name,
            'email': r.requested_by.email,
            'phone': r.business.phone or '',
            'amount': str(r.amount), 'upi_reference': r.upi_reference,
            'status': r.status,
            'created_at': r.created_at.strftime('%d-%m-%Y %H:%M'),
            'rejection_reason': r.rejection_reason,
            'note': r.note,
        } for r in qs[:100]]})


class AdminReviewPaymentAPIView(APIView):
    """ShopZen admin: APPROVE or REJECT a PENDING payment request — atomic,
    duplicate-proof, and premium is activated ONLY here after admin verification."""
    permission_classes = [IsAuthenticated, IsShopZenAdmin]

    def post(self, request, request_id):
        action = str(request.data.get('action', '')).upper()
        if action not in ('APPROVE', 'REJECT'):
            return Response({'error': 'action must be APPROVE or REJECT'},
                            status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # select_for_update prevents double-approval races/replays.
            req = SubscriptionPaymentRequest.objects.select_for_update().filter(
                pk=request_id, status='PENDING'
            ).first()
            if req is None:
                _audit(request.user, f'payment_{action.lower()}', f'request#{request_id}',
                       'already processed or missing', 'BLOCKED')
                return Response(
                    {'error': 'Request not found or already processed.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            business = req.business
            now = timezone.localtime()

            if action == 'APPROVE':
                months = req.months_purchased
                if months < 1:
                    months = 1
                base = max(business.subscription_end_date, now.date())
                business.subscription_start_date = now.date()
                business.subscription_end_date = base + timedelta(days=30 * months)
                business.subscription_status = 'ACTIVE'
                business.save(update_fields=[
                    'subscription_start_date', 'subscription_end_date', 'subscription_status'
                ])
                req.status = 'APPROVED'
                req.reviewed_by = request.user
                req.reviewed_at = now
                req.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
                _audit(request.user, 'subscription_approve', req.business.name,
                       f'request#{req.id} ₹{req.amount} ref={req.upi_reference} '
                       f'→ active till {business.subscription_end_date}')
                return Response({
                    'message': 'Subscription approved and activated.',
                    'new_expiry_date': business.subscription_end_date.strftime('%d-%m-%Y'),
                })
            else:
                reason = str(request.data.get('reason', '')).strip()
                req.status = 'REJECTED'
                req.reviewed_by = request.user
                req.reviewed_at = now
                req.rejection_reason = reason or 'Payment could not be verified.'
                req.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'rejection_reason'])
                _audit(request.user, 'subscription_reject', req.business.name,
                       f'request#{req.id} ₹{req.amount} — {req.rejection_reason}', 'REJECTED')
                return Response({'message': 'Payment request rejected.'})

