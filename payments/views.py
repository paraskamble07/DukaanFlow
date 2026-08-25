from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from core.utils import business_required, build_whatsapp_url, format_inr
from .models import Payment
from .forms import CustomerPaymentForm, SupplierPaymentForm
from customers.models import Customer
from suppliers.models import Supplier

@business_required
def payment_list(request):
    business = request.business
    p_type = request.GET.get('type', '')
    query = request.GET.get('q', '').strip()
    
    payments = Payment.objects.filter(business=business).select_related('customer', 'supplier', 'sale')
    
    if p_type:
        payments = payments.filter(payment_type=p_type)
    if query:
        payments = payments.filter(
            Q(customer__name__icontains=query) |
            Q(customer__phone__icontains=query) |
            Q(supplier__company_name__icontains=query) |
            Q(reference_number__icontains=query)
        )
        
    total_received = Payment.objects.filter(business=business, payment_type='CUSTOMER_PAYMENT').aggregate(Sum('amount'))['amount__sum'] or 0
    total_paid_out = Payment.objects.filter(business=business, payment_type='SUPPLIER_PAYMENT').aggregate(Sum('amount'))['amount__sum'] or 0
    
    paginator = Paginator(payments, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'payments/payment_list.html', {
        'page_obj': page_obj,
        'p_type': p_type,
        'query': query,
        'total_received': total_received,
        'total_paid_out': total_paid_out,
    })

@business_required
def customer_payment_create(request):
    business = request.business
    cust_id = request.GET.get('customer')
    initial = {}
    if cust_id:
        initial['customer'] = cust_id
        
    if request.method == 'POST':
        form = CustomerPaymentForm(request.POST, business=business)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.business = business
            payment.payment_type = 'CUSTOMER_PAYMENT'
            payment.save()
            
            # Recalculate customer due
            cust = payment.customer
            rem_due = cust.get_outstanding_due()
            
            # Build WhatsApp receipt url
            wa_msg = f"Namaste {cust.name},\n\nWe have received your payment of *{format_inr(payment.amount)}* on {payment.payment_date}.\nRemaining Khata Balance: *{format_inr(rem_due)}*.\n\nThank you for shopping at *{business.name}*!"
            wa_url = build_whatsapp_url(cust.phone, wa_msg)
            
            messages.success(request, f"Payment of ₹{payment.amount} recorded for {cust.name}!")
            return render(request, 'payments/payment_receipt_success.html', {
                'payment': payment,
                'customer': cust,
                'remaining_due': rem_due,
                'wa_url': wa_url,
            })
    else:
        form = CustomerPaymentForm(initial=initial, business=business)
        
    return render(request, 'payments/customer_payment_form.html', {'form': form})

@business_required
def supplier_payment_create(request):
    business = request.business
    sup_id = request.GET.get('supplier')
    initial = {}
    if sup_id:
        initial['supplier'] = sup_id
        
    if request.method == 'POST':
        form = SupplierPaymentForm(request.POST, business=business)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.business = business
            payment.payment_type = 'SUPPLIER_PAYMENT'
            payment.save()
            messages.success(request, f"Payment voucher of ₹{payment.amount} recorded for {payment.supplier.company_name}!")
            return redirect('suppliers:detail', pk=payment.supplier.pk)
    else:
        form = SupplierPaymentForm(initial=initial, business=business)
        
    return render(request, 'payments/supplier_payment_form.html', {'form': form})
