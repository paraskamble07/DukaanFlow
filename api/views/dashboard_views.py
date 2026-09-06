from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from sales.models import Sale, SaleItem
from expenses.models import Expense
from payments.models import Payment
from customers.models import Customer
from suppliers.models import Supplier
from products.models import Product
from api.serializers import SaleSerializer, PaymentSerializer, ProductSerializer
from api.permissions import HasActiveBusiness

class DashboardAPIView(APIView):
    permission_classes = [HasActiveBusiness]

    def get(self, request):
        business = request.business
        # Local (IST) date so post-midnight sales count as "today" for the shop.
        today = timezone.localtime().date()
        tz = timezone.get_current_timezone()
        from datetime import datetime as _dt
        day_start = _dt(today.year, today.month, today.day, tzinfo=tz)
        next_day = day_start + timedelta(days=1)

        # 1. Today's KPIs
        today_sales_qs = Sale.objects.filter(business=business, sale_date__gte=day_start, sale_date__lt=next_day)
        today_sales = float(today_sales_qs.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'))
        today_sales_count = today_sales_qs.count()

        # Today's COGS
        today_cogs = Decimal('0.00')
        for item in SaleItem.objects.filter(sale__in=today_sales_qs).select_related('product'):
            today_cogs += item.product.purchase_price * Decimal(str(item.quantity))
        today_gross_profit = float(Decimal(str(today_sales)) - today_cogs)

        today_expenses = float(Expense.objects.filter(
            business=business, expense_date=today
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00'))

        today_net_profit = today_gross_profit - today_expenses

        # 2. Receivables & Payables
        customers = Customer.objects.filter(business=business)
        total_receivable = float(sum(c.get_outstanding_due() for c in customers))

        suppliers = Supplier.objects.filter(business=business)
        total_payable = float(sum(s.get_outstanding_due() for s in suppliers))

        # 3. Product & Stock KPIs
        products = Product.objects.filter(business=business)
        total_products_count = products.count()
        low_stock_products = [p for p in products if p.is_low_stock() or p.is_out_of_stock()]
        low_stock_count = len(low_stock_products)

        # 4. Weekly Sales & Expenses Trend (Last 7 days)
        chart_labels = []
        chart_sales_data = []
        chart_expense_data = []

        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            chart_labels.append(day.strftime('%a, %d %b'))

            d_start = _dt(day.year, day.month, day.day, tzinfo=tz)
            d_end = d_start + timedelta(days=1)
            day_sale = Sale.objects.filter(
                business=business, sale_date__gte=d_start, sale_date__lt=d_end
            ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            chart_sales_data.append(float(day_sale))

            day_exp = Expense.objects.filter(
                business=business, expense_date=day
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            chart_expense_data.append(float(day_exp))

        # 5. Recent Activity
        recent_sales = Sale.objects.filter(business=business).select_related('customer').order_by('-sale_date')[:6]
        recent_payments = Payment.objects.filter(business=business).select_related('customer', 'supplier').order_by('-payment_date')[:5]

        # 6. Pending Khata List (Top 5)
        pending_customers = []
        for c in customers:
            d = c.get_outstanding_due()
            if d > 0:
                pending_customers.append({
                    'id': c.id,
                    'name': c.name,
                    'phone': c.phone,
                    'due': float(d),
                    'whatsapp_reminder_url': c.get_whatsapp_reminder_url()
                })
        pending_customers.sort(key=lambda x: x['due'], reverse=True)

        return Response({
            'today': {
                'date': today.strftime('%d-%m-%Y'),
                'sales': today_sales,
                'sales_count': today_sales_count,
                'gross_profit': today_gross_profit,
                'net_profit': today_net_profit,
                'expenses': today_expenses,
            },
            'receivables': {
                'total_receivable': total_receivable,
                'total_payable': total_payable,
            },
            'inventory': {
                'total_products': total_products_count,
                'low_stock_count': low_stock_count,
                'low_stock_items': ProductSerializer(low_stock_products[:5], many=True, context={'request': request}).data
            },
            'charts': {
                'labels': chart_labels,
                'sales': chart_sales_data,
                'expenses': chart_expense_data,
            },
            'recent_sales': SaleSerializer(recent_sales, many=True).data,
            'recent_payments': PaymentSerializer(recent_payments, many=True).data,
            'top_pending_khata': pending_customers[:5],
        })
