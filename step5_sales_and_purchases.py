import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# --- 1. SUPPLIERS ---
# suppliers/models.py
suppliers_models = """from django.db import models
from decimal import Decimal
from core.models import TenantModel

class Supplier(TenantModel):
    name = models.CharField(max_length=150, verbose_name="Contact Person Name")
    company_name = models.CharField(max_length=200, verbose_name="Distributor / Company Name")
    phone = models.CharField(max_length=20, verbose_name="Phone Number")
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    gstin = models.CharField(max_length=25, blank=True, null=True, verbose_name="Supplier GSTIN")
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['company_name', 'name']

    def __str__(self):
        return f"{self.company_name} ({self.name})"

    def get_total_purchases(self):
        total = self.purchases_purchase_set.aggregate(models.Sum('total_amount'))['total_amount__sum']
        return total or Decimal('0.00')

    def get_total_paid(self):
        total = self.payments_payment_set.aggregate(models.Sum('amount'))['amount__sum']
        return total or Decimal('0.00')

    def get_outstanding_due(self):
        total_purchases = self.get_total_purchases()
        total_paid = self.get_total_paid()
        return max(Decimal('0.00'), total_purchases - total_paid)
"""
with open(os.path.join(BASE_DIR, "suppliers", "models.py"), "w", encoding="utf-8") as f:
    f.write(suppliers_models)

# suppliers/forms.py
suppliers_forms = """from django import forms
from .models import Supplier

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['company_name', 'name', 'phone', 'email', 'address', 'gstin', 'notes']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. National Mobile Distributors', 'required': True}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Rajesh Gupta', 'required': True}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 9820012345', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Optional email'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'City, State'}),
            'gstin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional GSTIN'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
"""
with open(os.path.join(BASE_DIR, "suppliers", "forms.py"), "w", encoding="utf-8") as f:
    f.write(suppliers_forms)

# suppliers/views.py
suppliers_views = """from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from core.utils import business_required
from .models import Supplier
from .forms import SupplierForm
from purchases.models import Purchase
from payments.models import Payment

@business_required
def supplier_list(request):
    business = request.business
    query = request.GET.get('q', '').strip()
    
    suppliers = Supplier.objects.filter(business=business)
    if query:
        suppliers = suppliers.filter(
            Q(name__icontains=query) | Q(company_name__icontains=query) | Q(phone__icontains=query)
        )
        
    sup_list = list(suppliers)
    for s in sup_list:
        s.total_purchases = s.get_total_purchases()
        s.total_paid_amt = s.get_total_paid()
        s.due_amt = s.get_outstanding_due()
        
    paginator = Paginator(sup_list, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    total_payable = sum(s.due_amt for s in sup_list)
    
    return render(request, 'suppliers/supplier_list.html', {
        'page_obj': page_obj,
        'query': query,
        'total_payable': total_payable,
    })

@business_required
def supplier_create(request):
    business = request.business
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.business = business
            supplier.save()
            messages.success(request, f"Supplier '{supplier.company_name}' added successfully!")
            return redirect('suppliers:detail', pk=supplier.pk)
    else:
        form = SupplierForm()
    return render(request, 'suppliers/supplier_form.html', {'form': form, 'title': 'Add Supplier'})

@business_required
def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk, business=request.business)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f"Supplier '{supplier.company_name}' updated successfully!")
            return redirect('suppliers:detail', pk=supplier.pk)
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'suppliers/supplier_form.html', {'form': form, 'supplier': supplier, 'title': 'Edit Supplier'})

@business_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk, business=request.business)
    purchases = Purchase.objects.filter(supplier=supplier, business=request.business).order_by('-purchase_date')
    payments = Payment.objects.filter(supplier=supplier, business=request.business).order_by('-payment_date')
    
    total_purchases = supplier.get_total_purchases()
    total_paid = supplier.get_total_paid()
    due = supplier.get_outstanding_due()
    
    return render(request, 'suppliers/supplier_detail.html', {
        'supplier': supplier,
        'purchases': purchases,
        'payments': payments,
        'total_purchases': total_purchases,
        'total_paid': total_paid,
        'due': due,
    })

@business_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk, business=request.business)
    if request.method == 'POST':
        name = supplier.company_name
        supplier.delete()
        messages.success(request, f"Supplier '{name}' removed.")
        return redirect('suppliers:list')
    return render(request, 'suppliers/supplier_confirm_delete.html', {'supplier': supplier})
"""
with open(os.path.join(BASE_DIR, "suppliers", "views.py"), "w", encoding="utf-8") as f:
    f.write(suppliers_views)

# suppliers/urls.py
suppliers_urls = """from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    path('', views.supplier_list, name='list'),
    path('add/', views.supplier_create, name='create'),
    path('<int:pk>/', views.supplier_detail, name='detail'),
    path('<int:pk>/edit/', views.supplier_update, name='update'),
    path('<int:pk>/delete/', views.supplier_delete, name='delete'),
]
"""
with open(os.path.join(BASE_DIR, "suppliers", "urls.py"), "w", encoding="utf-8") as f:
    f.write(suppliers_urls)

# suppliers/admin.py
suppliers_admin = """from django.contrib import admin
from .models import Supplier

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'name', 'phone', 'business')
    search_fields = ('company_name', 'name', 'phone')
"""
with open(os.path.join(BASE_DIR, "suppliers", "admin.py"), "w", encoding="utf-8") as f:
    f.write(suppliers_admin)


# --- 2. PURCHASES ---
# purchases/models.py
purchases_models = """from django.db import models
from decimal import Decimal
from django.utils import timezone
from core.models import TenantModel

class Purchase(TenantModel):
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('UPI', 'UPI / Online'),
        ('BANK', 'Bank Transfer / NEFT'),
        ('CREDIT', 'Supplier Credit (Khata)'),
    ]
    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.CASCADE, related_name='purchases')
    invoice_number = models.CharField(max_length=100, verbose_name="Supplier Bill / Invoice No.")
    purchase_date = models.DateField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-purchase_date', '-created_at']

    def __str__(self):
        return f"PO #{self.invoice_number} - {self.supplier.company_name} (₹{self.total_amount})"
        
    def save(self, *args, **kwargs):
        self.due_amount = max(Decimal('0.00'), self.total_amount - self.paid_amount)
        super().save(*args, **kwargs)

class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='purchase_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_cost = Decimal(str(self.quantity)) * Decimal(str(self.unit_cost))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
"""
with open(os.path.join(BASE_DIR, "purchases", "models.py"), "w", encoding="utf-8") as f:
    f.write(purchases_models)

# purchases/views.py
purchases_views = """from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from decimal import Decimal
from core.utils import business_required
from .models import Purchase, PurchaseItem
from suppliers.models import Supplier
from products.models import Product
from inventory.models import StockMovement
from payments.models import Payment

@business_required
def purchase_list(request):
    business = request.business
    purchases = Purchase.objects.filter(business=business).select_related('supplier')
    paginator = Paginator(purchases, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'purchases/purchase_list.html', {'page_obj': page_obj})

@business_required
def purchase_create(request):
    business = request.business
    suppliers = Supplier.objects.filter(business=business)
    products = Product.objects.filter(business=business)
    
    if not suppliers.exists():
        messages.warning(request, "Please add a supplier first before creating a purchase.")
        return redirect('suppliers:create')
    if not products.exists():
        messages.warning(request, "Please add products first before creating a purchase.")
        return redirect('products:create')
        
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        bill_no = request.POST.get('invoice_number', '').strip()
        purchase_date = request.POST.get('purchase_date')
        payment_method = request.POST.get('payment_method', 'CASH')
        paid_amount = Decimal(request.POST.get('paid_amount', '0') or '0')
        notes = request.POST.get('notes', '')
        
        product_ids = request.POST.getlist('product_id[]')
        quantities = request.POST.getlist('quantity[]')
        unit_costs = request.POST.getlist('unit_cost[]')
        
        if not product_ids:
            messages.error(request, "Please add at least one product item to the purchase.")
            return redirect('purchases:create')
            
        supplier = get_object_or_404(Supplier, pk=supplier_id, business=business)
        
        try:
            with transaction.atomic():
                total_purchase_amt = Decimal('0.00')
                items_to_create = []
                
                for p_id, qty_str, cost_str in zip(product_ids, quantities, unit_costs):
                    p_obj = get_object_or_404(Product, pk=p_id, business=business)
                    qty = int(qty_str)
                    cost = Decimal(cost_str)
                    line_total = Decimal(str(qty)) * cost
                    total_purchase_amt += line_total
                    items_to_create.append((p_obj, qty, cost, line_total))
                    
                purchase = Purchase.objects.create(
                    business=business,
                    supplier=supplier,
                    invoice_number=bill_no or f"BILL-{business.purchases_purchase_set.count() + 101}",
                    purchase_date=purchase_date,
                    total_amount=total_purchase_amt,
                    paid_amount=paid_amount,
                    due_amount=max(Decimal('0.00'), total_purchase_amt - paid_amount),
                    payment_method=payment_method,
                    notes=notes
                )
                
                for p_obj, qty, cost, line_total in items_to_create:
                    PurchaseItem.objects.create(
                        purchase=purchase,
                        product=p_obj,
                        quantity=qty,
                        unit_cost=cost,
                        total_cost=line_total
                    )
                    
                    # Update stock & log movement
                    old_stock = p_obj.stock_quantity
                    p_obj.stock_quantity += qty
                    p_obj.purchase_price = cost  # update latest purchase cost
                    p_obj.save(update_fields=['stock_quantity', 'purchase_price'])
                    
                    StockMovement.objects.create(
                        business=business,
                        product=p_obj,
                        movement_type='PURCHASE',
                        quantity=qty,
                        previous_stock=old_stock,
                        new_stock=p_obj.stock_quantity,
                        notes=f"Stock received from {supplier.company_name} (PO #{purchase.invoice_number})",
                        reference_id=purchase.invoice_number
                    )
                    
                # Create payment record if paid_amount > 0
                if paid_amount > 0:
                    Payment.objects.create(
                        business=business,
                        payment_type='SUPPLIER_PAYMENT',
                        supplier=supplier,
                        purchase=purchase,
                        amount=paid_amount,
                        payment_method=payment_method if payment_method != 'CREDIT' else 'CASH',
                        payment_date=purchase_date,
                        reference_number=f"PO-PAY-{purchase.invoice_number}",
                        notes=f"Payment for purchase #{purchase.invoice_number}"
                    )
                    
                messages.success(request, f"Purchase order #{purchase.invoice_number} saved & stock updated!")
                return redirect('purchases:detail', pk=purchase.pk)
                
        except Exception as e:
            messages.error(request, f"Error creating purchase: {str(e)}")
            return redirect('purchases:create')
            
    return render(request, 'purchases/purchase_form.html', {
        'suppliers': suppliers,
        'products': products,
    })

@business_required
def purchase_detail(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk, business=request.business)
    items = purchase.items.select_related('product')
    return render(request, 'purchases/purchase_detail.html', {'purchase': purchase, 'items': items})
"""
with open(os.path.join(BASE_DIR, "purchases", "views.py"), "w", encoding="utf-8") as f:
    f.write(purchases_views)

# purchases/urls.py
purchases_urls = """from django.urls import path
from . import views

app_name = 'purchases'

urlpatterns = [
    path('', views.purchase_list, name='list'),
    path('add/', views.purchase_create, name='create'),
    path('<int:pk>/', views.purchase_detail, name='detail'),
]
"""
with open(os.path.join(BASE_DIR, "purchases", "urls.py"), "w", encoding="utf-8") as f:
    f.write(purchases_urls)

# purchases/admin.py
purchases_admin = """from django.contrib import admin
from .models import Purchase, PurchaseItem

class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'supplier', 'total_amount', 'paid_amount', 'due_amount', 'purchase_date')
    list_filter = ('payment_method', 'business')
    search_fields = ('invoice_number', 'supplier__company_name')
    inlines = [PurchaseItemInline]
"""
with open(os.path.join(BASE_DIR, "purchases", "admin.py"), "w", encoding="utf-8") as f:
    f.write(purchases_admin)


# --- 3. SALES & POS ---
# sales/models.py
sales_models = """from django.db import models
from decimal import Decimal
from django.utils import timezone
from core.models import TenantModel

class Sale(TenantModel):
    PAYMENT_STATUS_CHOICES = [
        ('PAID', 'Fully Paid'),
        ('PARTIAL', 'Partially Paid (Khata)'),
        ('UNPAID', 'Credit / Unpaid'),
    ]
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('UPI', 'UPI (GPay / PhonePe / Paytm)'),
        ('CARD', 'Debit / Credit Card'),
        ('BANK', 'Net Banking / Transfer'),
        ('CREDIT', 'Customer Khata / Credit'),
    ]
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='sales')
    invoice_number = models.CharField(max_length=50, verbose_name="Invoice Number", db_index=True)
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="GST Amount (₹)")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PAID')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    
    sale_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-sale_date', '-created_at']
        constraints = [
            models.UniqueConstraint(fields=['business', 'invoice_number'], name='unique_invoice_per_business')
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name} (₹{self.total_amount})"

    def save(self, *args, **kwargs):
        self.due_amount = max(Decimal('0.00'), self.total_amount - self.paid_amount)
        if self.paid_amount >= self.total_amount:
            self.payment_status = 'PAID'
        elif self.paid_amount > 0:
            self.payment_status = 'PARTIAL'
        else:
            self.payment_status = 'UNPAID'
        super().save(*args, **kwargs)

    def get_cogs(self):
        \"\"\"Calculates Cost of Goods Sold for this sale.\"\"\"
        cogs = Decimal('0.00')
        for item in self.items.select_related('product'):
            cost = item.product.purchase_price
            cogs += cost * Decimal(str(item.quantity))
        return cogs

    def get_gross_profit(self):
        return self.total_amount - self.get_cogs()

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='sale_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    imei_numbers = models.CharField(max_length=255, blank=True, null=True, verbose_name="IMEI / Serial Numbers")

    def save(self, *args, **kwargs):
        line_sub = (Decimal(str(self.unit_price)) * Decimal(str(self.quantity))) - Decimal(str(self.discount))
        self.total_price = max(Decimal('0.00'), line_sub)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
"""
with open(os.path.join(BASE_DIR, "sales", "models.py"), "w", encoding="utf-8") as f:
    f.write(sales_models)

# sales/views.py
sales_views = """import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.http import JsonResponse
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from core.utils import business_required
from .models import Sale, SaleItem
from customers.models import Customer
from products.models import Product
from inventory.models import StockMovement, MobileDevice
from payments.models import Payment

@business_required
def pos_view(request):
    business = request.business
    customers = Customer.objects.filter(business=business)
    products = Product.objects.filter(business=business, stock_quantity__gt=0).select_related('category')
    available_devices = MobileDevice.objects.filter(business=business, status='IN_STOCK').select_related('product')
    
    return render(request, 'sales/pos.html', {
        'customers': customers,
        'products': products,
        'available_devices': available_devices,
    })

@business_required
def checkout_api(request):
    \"\"\"Atomic POS checkout handler.\"\"\"
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
        
    business = request.business
    try:
        data = json.loads(request.body)
        customer_id = data.get('customer_id')
        new_cust_name = data.get('new_customer_name', '').strip()
        new_cust_phone = data.get('new_customer_phone', '').strip()
        
        items_data = data.get('items', [])
        discount_val = Decimal(str(data.get('discount', '0') or '0'))
        tax_val = Decimal(str(data.get('tax', '0') or '0'))
        paid_val = Decimal(str(data.get('paid_amount', '0') or '0'))
        payment_method = data.get('payment_method', 'CASH')
        notes = data.get('notes', '')
        
        if not items_data:
            return JsonResponse({'success': False, 'error': 'Cart is empty. Please add items to sell.'}, status=400)
            
        with transaction.atomic():
            # Get or create customer
            if customer_id:
                customer = get_object_or_404(Customer, pk=customer_id, business=business)
            elif new_cust_name and new_cust_phone:
                customer = Customer.objects.create(
                    business=business,
                    name=new_cust_name,
                    phone=new_cust_phone
                )
            else:
                # Walk-in customer
                customer, _ = Customer.objects.get_or_create(
                    business=business,
                    phone='0000000000',
                    defaults={'name': 'Cash / Walk-in Customer'}
                )
                
            subtotal = Decimal('0.00')
            processed_items = []
            
            for item in items_data:
                p_id = item.get('product_id')
                qty = int(item.get('quantity', 1))
                price = Decimal(str(item.get('unit_price')))
                item_disc = Decimal(str(item.get('discount', '0') or '0'))
                device_id = item.get('device_id')
                
                product = get_object_or_404(Product, pk=p_id, business=business)
                
                if product.stock_quantity < qty:
                    return JsonResponse({
                        'success': False,
                        'error': f"Insufficient stock for '{product.name}'. Available: {product.stock_quantity}, Requested: {qty}"
                    }, status=400)
                    
                line_total = (price * Decimal(str(qty))) - item_disc
                subtotal += line_total
                processed_items.append((product, qty, price, item_disc, line_total, device_id))
                
            total_amt = max(Decimal('0.00'), (subtotal - discount_val) + tax_val)
            paid_amt = min(total_amt, paid_val) if payment_method != 'CREDIT' else Decimal('0.00')
            if payment_method == 'CASH' or payment_method == 'UPI' or payment_method == 'CARD' or payment_method == 'BANK':
                if paid_val == Decimal('0.00'):
                    paid_amt = total_amt
                else:
                    paid_amt = paid_val
                    
            invoice_no = business.generate_next_invoice_number()
            
            sale = Sale.objects.create(
                business=business,
                customer=customer,
                invoice_number=invoice_no,
                subtotal=subtotal,
                discount=discount_val,
                tax_amount=tax_val,
                total_amount=total_amt,
                paid_amount=paid_amt,
                due_amount=max(Decimal('0.00'), total_amt - paid_amt),
                payment_method=payment_method,
                notes=notes
            )
            
            for product, qty, price, item_disc, line_total, device_id in processed_items:
                imei_str = ""
                if device_id:
                    dev = MobileDevice.objects.filter(pk=device_id, business=business).first()
                    if dev:
                        imei_str = f"IMEI: {dev.imei_1}" + (f", {dev.imei_2}" if dev.imei_2 else "")
                        
                sale_item = SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=qty,
                    unit_price=price,
                    discount=item_disc,
                    total_price=line_total,
                    imei_numbers=imei_str
                )
                
                # Update device if IMEI tracked
                if device_id:
                    dev = MobileDevice.objects.filter(pk=device_id, business=business).first()
                    if dev:
                        dev.status = 'SOLD'
                        dev.customer = customer
                        dev.sale_item = sale_item
                        dev.sale_date = timezone.now()
                        if product.warranty_months > 0:
                            dev.warranty_expiry_date = timezone.now().date() + timedelta(days=product.warranty_months * 30)
                        dev.save()
                        
                # Update product stock & log movement
                old_stk = product.stock_quantity
                product.stock_quantity -= qty
                product.save(update_fields=['stock_quantity'])
                
                StockMovement.objects.create(
                    business=business,
                    product=product,
                    movement_type='SALE',
                    quantity=qty,
                    previous_stock=old_stk,
                    new_stock=product.stock_quantity,
                    notes=f"Sold to {customer.name} (Invoice #{sale.invoice_number})",
                    reference_id=sale.invoice_number
                )
                
            # Create payment voucher if paid_amt > 0
            if paid_amt > 0:
                Payment.objects.create(
                    business=business,
                    payment_type='CUSTOMER_PAYMENT',
                    customer=customer,
                    sale=sale,
                    amount=paid_amt,
                    payment_method=payment_method if payment_method != 'CREDIT' else 'CASH',
                    reference_number=f"INV-PAY-{sale.invoice_number}",
                    notes=f"Payment received for invoice #{sale.invoice_number}"
                )
                
            return JsonResponse({
                'success': True,
                'invoice_number': sale.invoice_number,
                'sale_id': sale.pk,
                'total_amount': str(sale.total_amount),
                'paid_amount': str(sale.paid_amount),
                'due_amount': str(sale.due_amount),
                'invoice_url': f"/invoices/{sale.pk}/",
                'print_url': f"/invoices/{sale.pk}/print/",
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@business_required
def sale_list(request):
    business = request.business
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    
    sales = Sale.objects.filter(business=business).select_related('customer')
    if query:
        sales = sales.filter(
            models.Q(invoice_number__icontains=query) |
            models.Q(customer__name__icontains=query) |
            models.Q(customer__phone__icontains=query)
        )
    if status_filter:
        sales = sales.filter(payment_status=status_filter)
        
    paginator = Paginator(sales, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'sales/sale_list.html', {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
    })

@business_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk, business=request.business)
    items = sale.items.select_related('product')
    payments = sale.payments.all()
    
    return render(request, 'sales/sale_detail.html', {
        'sale': sale,
        'items': items,
        'payments': payments,
    })
"""
with open(os.path.join(BASE_DIR, "sales", "views.py"), "w", encoding="utf-8") as f:
    f.write(sales_views)

# sales/urls.py
sales_urls = """from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('pos/', views.pos_view, name='pos'),
    path('api/checkout/', views.checkout_api, name='checkout_api'),
    path('', views.sale_list, name='list'),
    path('<int:pk>/', views.sale_detail, name='detail'),
]
"""
with open(os.path.join(BASE_DIR, "sales", "urls.py"), "w", encoding="utf-8") as f:
    f.write(sales_urls)

# sales/admin.py
sales_admin = """from django.contrib import admin
from .models import Sale, SaleItem

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'total_amount', 'paid_amount', 'due_amount', 'payment_status', 'sale_date')
    list_filter = ('payment_status', 'payment_method', 'business')
    search_fields = ('invoice_number', 'customer__name', 'customer__phone')
    inlines = [SaleItemInline]
"""
with open(os.path.join(BASE_DIR, "sales", "admin.py"), "w", encoding="utf-8") as f:
    f.write(sales_admin)

print("Phase 5 (Suppliers, Purchases, Sales & POS) created successfully!")
