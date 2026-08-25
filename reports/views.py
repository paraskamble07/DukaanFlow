import csv
from datetime import datetime, date, timedelta
from decimal import Decimal
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum, Q, F
from django.utils import timezone
from core.utils import business_required, format_inr
from sales.models import Sale, SaleItem
from purchases.models import Purchase
from expenses.models import Expense
from customers.models import Customer
from suppliers.models import Supplier
from products.models import Product

def get_date_range(filter_type, start_str=None, end_str=None):
    today = timezone.now().date()
    if filter_type == 'today':
        return today, today
    elif filter_type == 'yesterday':
        yest = today - timedelta(days=1)
        return yest, yest
    elif filter_type == 'this_week':
        start = today - timedelta(days=today.weekday())
        return start, today
    elif filter_type == 'this_month':
        start = today.replace(day=1)
        return start, today
    elif filter_type == 'last_month':
        first_this = today.replace(day=1)
        last_prev = first_this - timedelta(days=1)
        start_prev = last_prev.replace(day=1)
        return start_prev, last_prev
    elif filter_type == 'custom' and start_str and end_str:
        try:
            return datetime.strptime(start_str, '%Y-%m-%d').date(), datetime.strptime(end_str, '%Y-%m-%d').date()
        except Exception:
            return today - timedelta(days=30), today
    else:
        return today - timedelta(days=30), today

@business_required
def reports_index(request):
    return render(request, 'reports/index.html')

@business_required
def sales_report(request):
    business = request.business
    period = request.GET.get('period', 'this_month')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    export = request.GET.get('export', '')
    
    start, end = get_date_range(period, start_date, end_date)
    
    sales = Sale.objects.filter(
        business=business,
        sale_date__date__gte=start,
        sale_date__date__lte=end
    ).select_related('customer').order_by('-sale_date')
    
    total_sales = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    total_paid = sales.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0.00')
    total_due = sales.aggregate(Sum('due_amount'))['due_amount__sum'] or Decimal('0.00')
    
    if export == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="sales_report_{start}_to_{end}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Invoice No', 'Date', 'Customer', 'Phone', 'Subtotal', 'Discount', 'Total Amount', 'Paid', 'Due', 'Payment Method'])
        for s in sales:
            writer.writerow([
                s.invoice_number,
                s.sale_date.strftime('%d-%m-%Y'),
                s.customer.name,
                s.customer.phone,
                f"{s.subtotal:.2f}",
                f"{s.discount:.2f}",
                f"{s.total_amount:.2f}",
                f"{s.paid_amount:.2f}",
                f"{s.due_amount:.2f}",
                s.get_payment_method_display()
            ])
        return response
        
    return render(request, 'reports/sales_report.html', {
        'sales': sales,
        'period': period,
        'start_date': start.strftime('%Y-%m-%d'),
        'end_date': end.strftime('%Y-%m-%d'),
        'total_sales': total_sales,
        'total_paid': total_paid,
        'total_due': total_due,
    })

@business_required
def profit_loss_report(request):
    business = request.business
    period = request.GET.get('period', 'this_month')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    start, end = get_date_range(period, start_date, end_date)
    
    sales = Sale.objects.filter(
        business=business,
        sale_date__date__gte=start,
        sale_date__date__lte=end
    )
    
    total_revenue = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    
    # Calculate COGS
    total_cogs = Decimal('0.00')
    sale_items = SaleItem.objects.filter(
        sale__in=sales
    ).select_related('product')
    for item in sale_items:
        total_cogs += item.product.purchase_price * Decimal(str(item.quantity))
        
    gross_profit = total_revenue - total_cogs
    gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Business Expenses
    expenses = Expense.objects.filter(
        business=business,
        expense_date__gte=start,
        expense_date__lte=end
    )
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    
    net_profit = gross_profit - total_expenses
    net_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    expense_breakdown = Expense.objects.filter(
        business=business,
        expense_date__gte=start,
        expense_date__lte=end
    ).values('category__name').annotate(total=Sum('amount')).order_by('-total')
    
    return render(request, 'reports/profit_loss.html', {
        'period': period,
        'start_date': start.strftime('%Y-%m-%d'),
        'end_date': end.strftime('%Y-%m-%d'),
        'total_revenue': total_revenue,
        'total_cogs': total_cogs,
        'gross_profit': gross_profit,
        'gross_margin': round(gross_margin, 1),
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'net_margin': round(net_margin, 1),
        'expense_breakdown': expense_breakdown,
    })

@business_required
def khata_report(request):
    business = request.business
    export = request.GET.get('export', '')
    
    customers = Customer.objects.filter(business=business)
    khata_list = []
    for c in customers:
        due = c.get_outstanding_due()
        if due > 0:
            khata_list.append({
                'customer': c,
                'total_purchases': c.get_total_sales(),
                'total_paid': c.get_total_paid(),
                'due': due,
                'wa_url': c.get_whatsapp_reminder_url(),
            })
            
    khata_list.sort(key=lambda x: x['due'], reverse=True)
    total_due_all = sum(k['due'] for k in khata_list)
    
    if export == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="customer_khata_dues.csv"'
        writer = csv.writer(response)
        writer.writerow(['Customer Name', 'Mobile Number', 'Total Purchases (₹)', 'Total Paid (₹)', 'Outstanding Balance (₹)'])
        for k in khata_list:
            writer.writerow([
                k['customer'].name,
                k['customer'].phone,
                f"{k['total_purchases']:.2f}",
                f"{k['total_paid']:.2f}",
                f"{k['due']:.2f}"
            ])
        return response
        
    return render(request, 'reports/khata_report.html', {
        'khata_list': khata_list,
        'total_due_all': total_due_all,
    })

@business_required
def inventory_report(request):
    business = request.business
    export = request.GET.get('export', '')
    
    products = Product.objects.filter(business=business).select_related('category')
    
    total_items = sum(p.stock_quantity for p in products)
    total_cost_val = sum(p.stock_quantity * p.purchase_price for p in products)
    total_mrp_val = sum(p.stock_quantity * p.selling_price for p in products)
    
    if export == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventory_stock_valuation.csv"'
        writer = csv.writer(response)
        writer.writerow(['Product Name', 'Brand', 'Category', 'SKU', 'Cost Price (₹)', 'Selling Price (₹)', 'Stock Qty', 'Valuation Cost (₹)', 'Valuation MRP (₹)', 'Status'])
        for p in products:
            status = "Out of Stock" if p.is_out_of_stock() else ("Low Stock" if p.is_low_stock() else "In Stock")
            writer.writerow([
                p.name,
                p.brand or '',
                p.category.name if p.category else '',
                p.sku or '',
                f"{p.purchase_price:.2f}",
                f"{p.selling_price:.2f}",
                p.stock_quantity,
                f"{p.stock_quantity * p.purchase_price:.2f}",
                f"{p.stock_quantity * p.selling_price:.2f}",
                status
            ])
        return response
        
    return render(request, 'reports/inventory_report.html', {
        'products': products,
        'total_items': total_items,
        'total_cost_val': total_cost_val,
        'total_mrp_val': total_mrp_val,
    })
