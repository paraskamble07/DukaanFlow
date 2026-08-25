import json
from datetime import date, timedelta
from decimal import Decimal
from django.shortcuts import render, redirect
from django.db.models import Sum, Count, Q
from django.utils import timezone
from core.utils import business_required, format_inr
from sales.models import Sale, SaleItem
from expenses.models import Expense
from payments.models import Payment
from customers.models import Customer
from suppliers.models import Supplier
from products.models import Product

@business_required
def index(request):
    business = request.business
    today = timezone.now().date()
    
    # 1. Today's KPIs
    today_sales_qs = Sale.objects.filter(business=business, sale_date__date=today)
    today_sales = today_sales_qs.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    today_sales_count = today_sales_qs.count()
    
    # Today's COGS
    today_cogs = Decimal('0.00')
    for item in SaleItem.objects.filter(sale__in=today_sales_qs).select_related('product'):
        today_cogs += item.product.purchase_price * Decimal(str(item.quantity))
    today_gross_profit = today_sales - today_cogs
    
    today_expenses = Expense.objects.filter(
        business=business, expense_date=today
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    
    today_net_profit = today_gross_profit - today_expenses
    
    # 2. Receivables & Payables (Khata balances)
    customers = Customer.objects.filter(business=business)
    total_receivable = Decimal('0.00')
    for c in customers:
        total_receivable += c.get_outstanding_due()
        
    suppliers = Supplier.objects.filter(business=business)
    total_payable = Decimal('0.00')
    for s in suppliers:
        total_payable += s.get_outstanding_due()
        
    # 3. Product & Stock KPIs
    products = Product.objects.filter(business=business)
    total_products_count = products.count()
    low_stock_products = [p for p in products if p.is_low_stock() or p.is_out_of_stock()]
    low_stock_count = len(low_stock_products)
    
    # 4. Weekly Sales Chart Data (Last 7 Days)
    chart_labels = []
    chart_sales_data = []
    chart_expense_data = []
    
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_label = day.strftime('%a, %d %b')
        chart_labels.append(day_label)
        
        day_sale = Sale.objects.filter(
            business=business, sale_date__date=day
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        chart_sales_data.append(float(day_sale))
        
        day_exp = Expense.objects.filter(
            business=business, expense_date=day
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        chart_expense_data.append(float(day_exp))
        
    # 5. Recent Activity
    recent_sales = Sale.objects.filter(business=business).select_related('customer').order_by('-sale_date')[:6]
    recent_payments = Payment.objects.filter(business=business).select_related('customer', 'supplier').order_by('-payment_date')[:5]
    
    # 6. Outstanding Khata Reminders List (Top 5)
    pending_customers = []
    for c in customers:
        d = c.get_outstanding_due()
        if d > 0:
            pending_customers.append({
                'customer': c,
                'due': d,
                'wa_url': c.get_whatsapp_reminder_url()
            })
    pending_customers.sort(key=lambda x: x['due'], reverse=True)
    top_pending_customers = pending_customers[:5]
    
    return render(request, 'dashboard/index.html', {
        'today_sales': today_sales,
        'today_sales_count': today_sales_count,
        'today_gross_profit': today_gross_profit,
        'today_net_profit': today_net_profit,
        'today_expenses': today_expenses,
        'total_receivable': total_receivable,
        'total_payable': total_payable,
        'total_products_count': total_products_count,
        'low_stock_count': low_stock_count,
        'low_stock_products': low_stock_products[:5],
        'chart_labels': json.dumps(chart_labels),
        'chart_sales_data': json.dumps(chart_sales_data),
        'chart_expense_data': json.dumps(chart_expense_data),
        'recent_sales': recent_sales,
        'recent_payments': recent_payments,
        'top_pending_customers': top_pending_customers,
    })
