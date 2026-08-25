import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# customers/models.py
customers_models = """from django.db import models
from decimal import Decimal
from core.models import TenantModel
from core.utils import build_whatsapp_url, format_inr

class Customer(TenantModel):
    name = models.CharField(max_length=150, verbose_name="Customer Name")
    phone = models.CharField(max_length=15, verbose_name="Mobile / WhatsApp Number", db_index=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True, verbose_name="Address")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes / Khata Remarks")
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Credit Limit (₹)")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.phone})"

    def get_total_sales(self):
        total = self.sales_sale_set.aggregate(models.Sum('total_amount'))['total_amount__sum']
        return total or Decimal('0.00')

    def get_total_paid(self):
        # Payments directly attached to customer
        total_payments = self.payments_payment_set.aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0.00')
        return total_payments

    def get_outstanding_due(self):
        total_sales = self.get_total_sales()
        total_paid = self.get_total_paid()
        due = total_sales - total_paid
        return max(Decimal('0.00'), due)

    def get_whatsapp_reminder_url(self):
        due = self.get_outstanding_due()
        if due <= 0:
            return ""
        shop_name = self.business.name if self.business else "our shop"
        msg = f"Namaste {self.name},\\n\\nYour outstanding Khata balance with *{shop_name}* is *{format_inr(due)}*.\\n\\nPlease settle the payment at your earliest convenience.\\n\\nThank you!"
        return build_whatsapp_url(self.phone, msg)
"""
with open(os.path.join(BASE_DIR, "customers", "models.py"), "w", encoding="utf-8") as f:
    f.write(customers_models)

# customers/forms.py
customers_forms = """from django import forms
from .models import Customer

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email', 'address', 'credit_limit', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name', 'required': True}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit mobile number', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Optional email'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Locality, City'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Special notes or references'}),
        }
"""
with open(os.path.join(BASE_DIR, "customers", "forms.py"), "w", encoding="utf-8") as f:
    f.write(customers_forms)

# customers/views.py
customers_views = """from django.shortcuts import render, redirect, get_object_or_404
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
"""
with open(os.path.join(BASE_DIR, "customers", "views.py"), "w", encoding="utf-8") as f:
    f.write(customers_views)

# customers/urls.py
customers_urls = """from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.customer_list, name='list'),
    path('add/', views.customer_create, name='create'),
    path('<int:pk>/', views.customer_detail, name='detail'),
    path('<int:pk>/edit/', views.customer_update, name='update'),
    path('<int:pk>/delete/', views.customer_delete, name='delete'),
]
"""
with open(os.path.join(BASE_DIR, "customers", "urls.py"), "w", encoding="utf-8") as f:
    f.write(customers_urls)

# customers/admin.py
customers_admin = """from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'business', 'credit_limit', 'created_at')
    search_fields = ('name', 'phone', 'email', 'business__name')
    list_filter = ('business', 'created_at')
"""
with open(os.path.join(BASE_DIR, "customers", "admin.py"), "w", encoding="utf-8") as f:
    f.write(customers_admin)

print("Phase 3 (Customers & Khata) created successfully!")
