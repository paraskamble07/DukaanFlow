from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from sales.models import Sale, SaleItem
from expenses.models import Expense
from customers.models import Customer
from suppliers.models import Supplier
from products.models import Product
from purchases.models import Purchase
from api.permissions import HasActiveBusiness


def parse_report_dates(request):
    """Shared period parser: today / yesterday / 7d / 30d / this_month / last_month / custom."""
    # Use the shop's local (IST) date — a sale made after IST midnight must
    # show in "today", not under the previous UTC day.
    today = timezone.localtime().date()
    params = request.query_params
    period = params.get('period', 'this_month')

    if period == 'today':
        return today, today
    elif period == 'yesterday':
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
    elif period == 'this_week':
        return today - timedelta(days=today.weekday()), today
    elif period == '7d':
        return today - timedelta(days=6), today
    elif period == '30d':
        return today - timedelta(days=29), today
    elif period == 'this_month':
        return today.replace(day=1), today
    elif period == 'last_month':
        first_this = today.replace(day=1)
        last_prev = first_this - timedelta(days=1)
        return last_prev.replace(day=1), last_prev
    elif period == 'custom':
        start_str = params.get('start_date')
        end_str = params.get('end_date')
        if start_str and end_str:
            from datetime import datetime
            try:
                return (
                    datetime.strptime(start_str, '%Y-%m-%d').date(),
                    datetime.strptime(end_str, '%Y-%m-%d').date(),
                )
            except ValueError:
                pass
    return today - timedelta(days=29), today


def local_dt_range(start, end):
    """Convert local (IST) calendar dates to an aware datetime range
    [start 00:00, end+1 00:00) so DateTimeField filters follow shop-local
    day boundaries instead of UTC."""
    tz = timezone.get_current_timezone()
    from datetime import datetime as _dt
    lo = _dt(start.year, start.month, start.day, tzinfo=tz)
    hi = _dt(end.year, end.month, end.day, tzinfo=tz) + timedelta(days=1)
    return lo, hi


class SalesReportAPIView(APIView):
    permission_classes = [HasActiveBusiness]

    def get(self, request):
        business = request.business
        start, end = parse_report_dates(request)
        lo, hi = local_dt_range(start, end)

        sales = Sale.objects.filter(
            business=business, sale_date__gte=lo, sale_date__lt=hi
        ).select_related('customer')

        total_amount = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        total_collected = sales.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0.00')
        total_due = sales.aggregate(Sum('due_amount'))['due_amount__sum'] or Decimal('0.00')

        total_cogs = Decimal('0.00')
        for item in SaleItem.objects.filter(sale__in=sales).select_related('product'):
            total_cogs += item.product.purchase_price * Decimal(str(item.quantity))

        # Day-by-day trend for chart rendering
        trend = []
        day = start
        while day <= end:
            dlo, dhi = local_dt_range(day, day)
            day_amount = Sale.objects.filter(
                business=business, sale_date__gte=dlo, sale_date__lt=dhi
            ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
            trend.append({
                'date': day.strftime('%d %b'),
                'amount': float(day_amount),
            })
            day += timedelta(days=1)

        # Payment mode split
        mode_split = list(sales.values('payment_method').annotate(
            total=Sum('total_amount'), count=Count('id')
        ))

        return Response({
            'start_date': start.strftime('%Y-%m-%d'),
            'end_date': end.strftime('%Y-%m-%d'),
            'total_sales_count': sales.count(),
            'total_amount': float(total_amount),
            'total_collected': float(total_collected),
            'total_due': float(total_due),
            'total_cogs': float(total_cogs),
            'gross_profit': float(total_amount - total_cogs),
            'trend': trend[:62],
            'mode_split': [
                {'payment_method': m['payment_method'], 'total': float(m['total'] or 0)}
                for m in mode_split
            ],
        })


class StockReportAPIView(APIView):
    permission_classes = [HasActiveBusiness]

    def get(self, request):
        business = request.business
        products = Product.objects.filter(business=business).select_related('category')

        total_units = 0
        cost_value = Decimal('0.00')
        selling_value = Decimal('0.00')
        low_stock = []
        out_of_stock = []
        dead_stock = []

        cutoff = timezone.now().date() - timedelta(days=60)
        for p in products:
            units = p.stock_quantity
            total_units += units
            cost_value += p.purchase_price * Decimal(str(units))
            selling_value += p.selling_price * Decimal(str(units))

            if p.is_out_of_stock():
                out_of_stock.append(p)
            elif p.is_low_stock():
                low_stock.append(p)

            last_sale = SaleItem.objects.filter(
                product=p, sale__business=business
            ).order_by('-sale__sale_date').first()
            last_sale_date = last_sale.sale.sale_date if last_sale else None
            if units > 0 and (last_sale_date is None or last_sale_date.date() <= cutoff):
                dead_stock.append({
                    'id': p.id,
                    'name': p.name,
                    'brand': p.brand,
                    'quantity': units,
                    'investment': float(p.purchase_price * Decimal(str(units))),
                    'last_sale': last_sale_date.strftime('%d-%m-%Y') if last_sale_date else 'Never sold',
                })

        return Response({
            'total_products': products.count(),
            'total_units': total_units,
            'stock_cost_value': float(cost_value),
            'stock_selling_value': float(selling_value),
            'potential_margin': float(selling_value - cost_value),
            'low_stock_count': len(low_stock),
            'out_of_stock_count': len(out_of_stock),
            'low_stock_items': [
                {'id': p.id, 'name': p.name, 'brand': p.brand,
                 'stock': p.stock_quantity, 'min_stock': p.min_stock}
                for p in low_stock[:15]
            ],
            'out_of_stock_items': [
                {'id': p.id, 'name': p.name, 'brand': p.brand} for p in out_of_stock[:15]
            ],
            'dead_stock': dead_stock[:20],
        })


class KhataReportAPIView(APIView):
    permission_classes = [HasActiveBusiness]

    def get(self, request):
        business = request.business
        customers = Customer.objects.filter(business=business)

        khata_list = []
        total_due = Decimal('0.00')
        for c in customers:
            due = c.get_outstanding_due()
            if due > 0:
                total_due += due
                last_payment = c.payments.filter(
                    payment_type='CUSTOMER_PAYMENT'
                ).order_by('-payment_date').first()
                khata_list.append({
                    'id': c.id,
                    'name': c.name,
                    'phone': c.phone,
                    'total_sales': float(c.get_total_sales()),
                    'total_paid': float(c.get_total_paid()),
                    'due': float(due),
                    'last_payment_date': last_payment.payment_date.strftime('%d-%m-%Y') if last_payment else None,
                    'whatsapp_reminder_url': c.get_whatsapp_reminder_url(),
                })

        khata_list.sort(key=lambda x: x['due'], reverse=True)

        suppliers = Supplier.objects.filter(business=business)
        supplier_payables = []
        total_payable = Decimal('0.00')
        for s in suppliers:
            due = s.get_outstanding_due()
            if due > 0:
                total_payable += due
                supplier_payables.append({
                    'id': s.id,
                    'name': s.company_name,
                    'phone': s.phone,
                    'total_purchases': float(s.get_total_purchases()),
                    'total_paid': float(s.get_total_paid()),
                    'due': float(due),
                })

        return Response({
            'customer_khata': khata_list,
            'total_customer_due': float(total_due),
            'supplier_payables': supplier_payables,
            'total_supplier_due': float(total_payable),
        })


class ExpenseReportAPIView(APIView):
    permission_classes = [HasActiveBusiness]

    def get(self, request):
        business = request.business
        start, end = parse_report_dates(request)

        expenses = Expense.objects.filter(
            business=business, expense_date__gte=start, expense_date__lte=end
        ).select_related('category')

        total = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')

        category_breakdown = list(expenses.values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total'))

        trend = []
        day = start
        while day <= end:
            day_amount = Expense.objects.filter(
                business=business, expense_date=day
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            trend.append({'date': day.strftime('%d %b'), 'amount': float(day_amount)})
            day += timedelta(days=1)

        return Response({
            'start_date': start.strftime('%Y-%m-%d'),
            'end_date': end.strftime('%Y-%m-%d'),
            'total_expenses': float(total),
            'expense_count': expenses.count(),
            'category_breakdown': [
                {'category': c['category__name'] or 'Uncategorised', 'total': float(c['total'])}
                for c in category_breakdown
            ],
            'trend': trend[:62],
        })

class GSTReportAPIView(APIView):
    permission_classes = [HasActiveBusiness]

    def get(self, request):
        business = request.business
        start, end = parse_report_dates(request)
        lo, hi = local_dt_range(start, end)

        sales = Sale.objects.filter(
            business=business, sale_date__gte=lo, sale_date__lt=hi
        ).select_related('customer')

        total_taxable = sales.aggregate(Sum('subtotal'))['subtotal__sum'] or Decimal('0.00')
        total_gst = sales.aggregate(Sum('tax_amount'))['tax_amount__sum'] or Decimal('0.00')
        total_invoices = sales.count()

        purchase_tax = Decimal('0.00')
        purchases = Purchase.objects.filter(
            business=business, purchase_date__gte=start, purchase_date__lte=end
        )
        # Purchases carry GST inside unit_cost; expose totals for accountant reference
        purchase_total = purchases.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

        gst_sales = [
            {
                'invoice_number': s.invoice_number,
                'date': s.sale_date.strftime('%d-%m-%Y'),
                'customer': s.customer.name,
                'taxable_value': float(s.subtotal),
                'gst': float(s.tax_amount),
                'total': float(s.total_amount),
            }
            for s in sales.order_by('-sale_date')[:100]
        ]

        return Response({
            'start_date': start.strftime('%Y-%m-%d'),
            'end_date': end.strftime('%Y-%m-%d'),
            'total_taxable_value': float(total_taxable),
            'total_gst_collected': float(total_gst),
            'total_invoices': total_invoices,
            'total_purchases_value': float(purchase_total),
            'sales': gst_sales,
        })


class TopProductsReportAPIView(APIView):
    permission_classes = [HasActiveBusiness]

    def get(self, request):
        business = request.business
        start, end = parse_report_dates(request)

        lo, hi = local_dt_range(start, end)
        items = SaleItem.objects.filter(
            sale__business=business,
            sale__sale_date__gte=lo,
            sale__sale_date__lt=hi,
        ).select_related('product', 'sale')

        product_stats = {}
        for item in items:
            key = item.product.id
            if key not in product_stats:
                product_stats[key] = {
                    'id': item.product.id,
                    'name': item.product.name,
                    'brand': item.product.brand,
                    'units_sold': 0,
                    'revenue': Decimal('0.00'),
                    'profit': Decimal('0.00'),
                }
            product_stats[key]['units_sold'] += item.quantity
            product_stats[key]['revenue'] += item.total_price
            product_stats[key]['profit'] += item.total_price - (
                item.product.purchase_price * Decimal(str(item.quantity))
            )

        top_products = sorted(product_stats.values(), key=lambda x: x['revenue'], reverse=True)[:20]

        brand_stats = {}
        for p in product_stats.values():
            brand = p['brand'] or 'Other'
            if brand not in brand_stats:
                brand_stats[brand] = {'brand': brand, 'units_sold': 0, 'revenue': Decimal('0.00')}
            brand_stats[brand]['units_sold'] += p['units_sold']
            brand_stats[brand]['revenue'] += p['revenue']
        top_brands = sorted(brand_stats.values(), key=lambda x: x['revenue'], reverse=True)[:10]

        return Response({
            'start_date': start.strftime('%Y-%m-%d'),
            'end_date': end.strftime('%Y-%m-%d'),
            'top_products': [
                {**p, 'revenue': float(p['revenue']), 'profit': float(p['profit'])}
                for p in top_products
            ],
            'top_brands': [
                {**b, 'revenue': float(b['revenue'])} for b in top_brands
            ],
        })


class TopCustomersReportAPIView(APIView):
    permission_classes = [HasActiveBusiness]

    def get(self, request):
        business = request.business
        start, end = parse_report_dates(request)

        lo, hi = local_dt_range(start, end)
        sales = Sale.objects.filter(
            business=business, sale_date__gte=lo, sale_date__lt=hi
        ).select_related('customer')

        customer_stats = {}
        for s in sales:
            key = s.customer.id
            if key not in customer_stats:
                customer_stats[key] = {
                    'id': s.customer.id,
                    'name': s.customer.name,
                    'phone': s.customer.phone,
                    'visits': 0,
                    'total_spent': Decimal('0.00'),
                }
            customer_stats[key]['visits'] += 1
            customer_stats[key]['total_spent'] += s.total_amount

        top_customers = sorted(customer_stats.values(), key=lambda x: x['total_spent'], reverse=True)[:20]

        return Response({
            'start_date': start.strftime('%Y-%m-%d'),
            'end_date': end.strftime('%Y-%m-%d'),
            'top_customers': [
                {**c, 'total_spent': float(c['total_spent'])} for c in top_customers
            ],
        })

class ProfitLossReportAPIView(APIView):
    permission_classes = [HasActiveBusiness]

    def get(self, request):
        business = request.business
        start, end = parse_report_dates(request)
        lo, hi = local_dt_range(start, end)

        sales = Sale.objects.filter(
            business=business,
            sale_date__gte=lo,
            sale_date__lt=hi
        )
        total_revenue = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

        total_cogs = Decimal('0.00')
        for item in SaleItem.objects.filter(sale__in=sales).select_related('product'):
            total_cogs += item.product.purchase_price * Decimal(str(item.quantity))

        gross_profit = total_revenue - total_cogs
        gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0

        expenses = Expense.objects.filter(
            business=business,
            expense_date__gte=start,
            expense_date__lte=end
        )
        total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')

        net_profit = gross_profit - total_expenses
        net_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

        expense_breakdown = list(Expense.objects.filter(
            business=business,
            expense_date__gte=start,
            expense_date__lte=end
        ).values('category__name').annotate(total=Sum('amount')).order_by('-total'))

        return Response({
            'start_date': start.strftime('%Y-%m-%d'),
            'end_date': end.strftime('%Y-%m-%d'),
            'total_revenue': float(total_revenue),
            'total_cogs': float(total_cogs),
            'gross_profit': float(gross_profit),
            'gross_margin_percent': round(float(gross_margin), 1),
            'total_expenses': float(total_expenses),
            'net_profit': float(net_profit),
            'net_margin_percent': round(float(net_margin), 1),
            'expense_breakdown': expense_breakdown,
        })
