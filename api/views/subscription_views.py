from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from businesses.models import SHOPZEN_PREMIUM_PRICE, Business
from api.serializers import BusinessSerializer
from api.permissions import HasActiveBusiness

class SubscriptionStatusAPIView(APIView):
    permission_classes = [HasActiveBusiness]

    def get(self, request):
        business = request.business
        days_left = business.days_until_expiry()
        is_active = business.is_subscription_active()

        return Response({
            'plan_name': 'ShopZen Premium',
            'price': SHOPZEN_PREMIUM_PRICE,
            'price_display': f'₹{SHOPZEN_PREMIUM_PRICE}/month',
            'status': 'ACTIVE' if is_active else 'EXPIRED',
            'is_active': is_active,
            'start_date': business.subscription_start_date.strftime('%d-%m-%Y'),
            'end_date': business.subscription_end_date.strftime('%d-%m-%Y'),
            'days_remaining': days_left,
            'features': [
                'Unlimited Products & Inventory',
                'Unlimited Customers & Digital Khata',
                'Lightning Fast POS Counter Billing',
                'Dual IMEI & Serial Tracker',
                '1-Click WhatsApp Reminders (Zero API fee)',
                'GST Ready PDF Invoices & Thermal Print',
                'Supplier Purchases & Expense Tracking',
                'True Gross & Net Profit Analytics',
                'Cloud Backup & Multi-Device Sync',
                'Offline POS Mode with Auto-Sync',
            ]
        })

class SubscriptionRenewAPIView(APIView):
    permission_classes = [HasActiveBusiness]

    def post(self, request):
        business = request.business
        # Server-side renewal logic (e.g. 30 days extension)
        today = timezone.now().date()
        base_date = business.subscription_end_date if business.subscription_end_date > today else today
        business.subscription_end_date = base_date + timedelta(days=30)
        business.subscription_status = 'ACTIVE'
        business.save(update_fields=['subscription_end_date', 'subscription_status'])

        return Response({
            'message': 'ShopZen Premium subscription renewed successfully for 30 days!',
            'new_expiry_date': business.subscription_end_date.strftime('%d-%m-%Y'),
            'status': 'ACTIVE'
        })
