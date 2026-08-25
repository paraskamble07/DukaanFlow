from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from decimal import Decimal
from core.utils import business_required
from .models import Customer
from .forms import CustomerForm
from sales.models import Sale
from payments.models import Payment

@business_required
def customer_list(request):
    business = request.business
    query = request.GET.get('q', '').strip()
    due_filter = request.GET.get('due', '')
    
    customers = Customer.objects.filter(business=business)
    
    if query:
        customers = customers.filter(
            Q(name__icontains=query) | Q(phone__icontains=query) | Q(address__icontains=query)
        )
        
    customers_list = list(customers)
    # Calculate Khata balances
    for c in customers_list:
        c.total_purchases = c.get_total_sales()
        c.total_paid_amt = c.get_total_paid()
        c.due_amt = c.get_outstanding_due()
        c.wa_link = c.get_whatsapp_reminder_url()

    if due_filter == 'yes':
        customers_list = [c for c in customers_list if c.due_amt > 0]
    elif due_filter == 'cleared':
        customers_list = [c for c in customers_list if c.due_amt <= 0]
        
    paginator = Paginator(customers_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    can_add, current_count, max_limit = business.can_add_customer()
    
    total_market_due = sum(c.due_amt for c in customers_list)
    
    return render(request, 'customers/customer_list.html', {
        'page_obj': page_obj,
        'query': query,
        'due_filter': due_filter,
        'can_add': can_add,
        'current_count': current_count,
        'max_limit': max_limit,
        'total_market_due': total_market_due,
    })

@business_required
def customer_create(request):
    business = request.business
    can_add, count, limit = business.can_add_customer()
    if not can_add:
        messages.error(
            request,
            f"You have reached the Free Plan limit of {limit} customers. Please upgrade to Pro for unlimited customers."
        )
        return redirect('businesses:plans')
        
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.business = business
            customer.save()
            messages.success(request, f"Customer '{customer.name}' added successfully!")
            return redirect('customers:detail', pk=customer.pk)
    else:
        form = CustomerForm()
        
    return render(request, 'customers/customer_form.html', {
        'form': form,
        'title': 'Add New Customer',
        'is_edit': False
    })

@business_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk, business=request.business)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f"Customer '{customer.name}' updated successfully!")
            return redirect('customers:detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
        
    return render(request, 'customers/customer_form.html', {
        'form': form,
        'customer': customer,
        'title': f'Edit Customer - {customer.name}',
        'is_edit': True
    })

@business_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk, business=request.business)
    sales = Sale.objects.filter(customer=customer, business=request.business).order_by('-sale_date')
    payments = Payment.objects.filter(customer=customer, business=request.business).order_by('-payment_date')
    
    total_sales = customer.get_total_sales()
    total_paid = customer.get_total_paid()
    due = customer.get_outstanding_due()
    wa_reminder = customer.get_whatsapp_reminder_url()
    
    return render(request, 'customers/customer_detail.html', {
        'customer': customer,
        'sales': sales,
        'payments': payments,
        'total_sales': total_sales,
        'total_paid': total_paid,
        'due': due,
        'wa_reminder': wa_reminder,
    })

@business_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk, business=request.business)
    if request.method == 'POST':
        name = customer.name
        customer.delete()
        messages.success(request, f"Customer '{name}' deleted successfully.")
        return redirect('customers:list')
    return render(request, 'customers/customer_confirm_delete.html', {'customer': customer})
