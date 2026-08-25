import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# --- 1. PRODUCTS ---
# products/models.py
products_models = """from django.db import models
from decimal import Decimal
from core.models import TenantModel

DEFAULT_CATEGORIES = [
    'Smartphones',
    'Feature Phones',
    'Chargers',
    'Cables',
    'Earphones',
    'Covers',
    'Tempered Glass',
    'Power Banks',
    'Smart Watches',
    'Other Accessories'
]

class Category(TenantModel):
    name = models.CharField(max_length=100, verbose_name="Category Name")
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['business', 'name'], name='unique_category_per_business')
        ]

    def __str__(self):
        return self.name

class Product(TenantModel):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=200, verbose_name="Product Name")
    brand = models.CharField(max_length=100, blank=True, null=True, verbose_name="Brand / Manufacturer")
    sku = models.CharField(max_length=100, blank=True, null=True, verbose_name="SKU Code")
    barcode = models.CharField(max_length=100, blank=True, null=True, verbose_name="Barcode / EAN")
    
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Purchase Cost (₹)")
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Selling Price / MRP (₹)")
    
    stock_quantity = models.IntegerField(default=0, verbose_name="Current Stock Quantity")
    min_stock = models.IntegerField(default=5, verbose_name="Low Stock Alert Threshold")
    
    warranty_months = models.PositiveIntegerField(default=0, verbose_name="Warranty Period (Months)")
    is_imei_tracked = models.BooleanField(default=False, verbose_name="Track Serial / IMEI Numbers (Mobile Phones)")
    
    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.SET_NULL, null=True, blank=True, related_name='supplied_products')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Product Image")
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['business', 'sku'], name='unique_sku_per_business')
        ]

    def __str__(self):
        brand_str = f"[{self.brand}] " if self.brand else ""
        return f"{brand_str}{self.name} - ₹{self.selling_price}"

    def is_low_stock(self):
        return 0 < self.stock_quantity <= self.min_stock

    def is_out_of_stock(self):
        return self.stock_quantity <= 0

    def get_profit_margin(self):
        if self.selling_price and self.selling_price > 0:
            diff = self.selling_price - self.purchase_price
            return (diff / self.selling_price) * 100
        return 0
"""
with open(os.path.join(BASE_DIR, "products", "models.py"), "w", encoding="utf-8") as f:
    f.write(products_models)

# products/forms.py
products_forms = """from django import forms
from .models import Product, Category

class ProductForm(forms.ModelForm):
    category_name = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Or type new category e.g. Chargers'})
    )

    class Meta:
        model = Product
        fields = [
            'name', 'brand', 'category', 'sku', 'barcode',
            'purchase_price', 'selling_price', 'stock_quantity', 'min_stock',
            'warranty_months', 'is_imei_tracked', 'supplier', 'image', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Samsung Galaxy A56 5G', 'required': True}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Samsung, Apple, Realme'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional SKU code'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Scan or enter barcode'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'required': True}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'required': True}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'required': True}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-control', 'value': 5}),
            'warranty_months': forms.NumberInput(attrs={'class': 'form-control', 'value': 12}),
            'is_imei_tracked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        if business:
            self.fields['category'].queryset = Category.objects.filter(business=business)
            from suppliers.models import Supplier
            self.fields['supplier'].queryset = Supplier.objects.filter(business=business)
"""
with open(os.path.join(BASE_DIR, "products", "forms.py"), "w", encoding="utf-8") as f:
    f.write(products_forms)

# products/views.py
products_views = """from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from decimal import Decimal
from core.utils import business_required
from .models import Product, Category, DEFAULT_CATEGORIES
from .forms import ProductForm
from inventory.models import StockMovement

def ensure_default_categories(business):
    for cat_name in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(business=business, name=cat_name)

@business_required
def product_list(request):
    business = request.business
    ensure_default_categories(business)
    
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    stock_status = request.GET.get('stock', '')
    
    products = Product.objects.filter(business=business).select_related('category', 'supplier')
    
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(brand__icontains=query) |
            Q(sku__icontains=query) |
            Q(barcode__icontains=query)
        )
        
    if category_id:
        products = products.filter(category_id=category_id)
        
    if stock_status == 'low':
        # stock <= min_stock and stock > 0
        products = [p for p in products if p.is_low_stock()]
    elif stock_status == 'out':
        products = [p for p in products if p.is_out_of_stock()]
    elif stock_status == 'in_stock':
        products = [p for p in products if p.stock_quantity > p.min_stock]
        
    categories = Category.objects.filter(business=business)
    can_add, current_count, max_limit = business.can_add_product()
    
    paginator = Paginator(list(products), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'products/product_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_id,
        'stock_status': stock_status,
        'query': query,
        'can_add': can_add,
        'current_count': current_count,
        'max_limit': max_limit,
    })

@business_required
def product_create(request):
    business = request.business
    ensure_default_categories(business)
    
    can_add, count, limit = business.can_add_product()
    if not can_add:
        messages.error(
            request,
            f"You have reached the Free Plan limit of {limit} products. Please upgrade to Pro for unlimited products."
        )
        return redirect('businesses:plans')
        
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, business=business)
        if form.is_valid():
            product = form.save(commit=False)
            product.business = business
            
            cat_name = form.cleaned_data.get('category_name')
            if cat_name:
                cat_obj, _ = Category.objects.get_or_create(business=business, name=cat_name.strip())
                product.category = cat_obj
                
            product.save()
            
            # Initial stock movement log if initial stock > 0
            if product.stock_quantity > 0:
                StockMovement.objects.create(
                    business=business,
                    product=product,
                    movement_type='ADJUSTMENT',
                    quantity=product.stock_quantity,
                    previous_stock=0,
                    new_stock=product.stock_quantity,
                    notes="Initial inventory stock on product creation"
                )
                
            messages.success(request, f"Product '{product.name}' added successfully!")
            return redirect('products:detail', pk=product.pk)
    else:
        form = ProductForm(business=business)
        
    return render(request, 'products/product_form.html', {
        'form': form,
        'title': 'Add New Product / Accessory',
        'is_edit': False
    })

@business_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk, business=request.business)
    old_stock = product.stock_quantity
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product, business=request.business)
        if form.is_valid():
            updated_product = form.save(commit=False)
            cat_name = form.cleaned_data.get('category_name')
            if cat_name:
                cat_obj, _ = Category.objects.get_or_create(business=request.business, name=cat_name.strip())
                updated_product.category = cat_obj
            updated_product.save()
            
            # Log stock movement if stock adjusted manually
            if updated_product.stock_quantity != old_stock:
                diff = updated_product.stock_quantity - old_stock
                StockMovement.objects.create(
                    business=request.business,
                    product=updated_product,
                    movement_type='ADJUSTMENT',
                    quantity=abs(diff),
                    previous_stock=old_stock,
                    new_stock=updated_product.stock_quantity,
                    notes=f"Manual stock adjustment from {old_stock} to {updated_product.stock_quantity}"
                )
                
            messages.success(request, f"Product '{product.name}' updated successfully!")
            return redirect('products:detail', pk=product.pk)
    else:
        form = ProductForm(instance=product, business=request.business)
        
    return render(request, 'products/product_form.html', {
        'form': form,
        'product': product,
        'title': f'Edit Product - {product.name}',
        'is_edit': True
    })

@business_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, business=request.business)
    stock_movements = StockMovement.objects.filter(product=product, business=request.business).order_by('-created_at')[:15]
    imei_devices = product.devices.filter(business=request.business).order_by('-created_at')[:20] if product.is_imei_tracked else []
    
    return render(request, 'products/product_detail.html', {
        'product': product,
        'stock_movements': stock_movements,
        'imei_devices': imei_devices,
    })

@business_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, business=request.business)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f"Product '{name}' deleted.")
        return redirect('products:list')
    return render(request, 'products/product_confirm_delete.html', {'product': product})
"""
with open(os.path.join(BASE_DIR, "products", "views.py"), "w", encoding="utf-8") as f:
    f.write(products_views)

# products/urls.py
products_urls = """from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('add/', views.product_create, name='create'),
    path('<int:pk>/', views.product_detail, name='detail'),
    path('<int:pk>/edit/', views.product_update, name='update'),
    path('<int:pk>/delete/', views.product_delete, name='delete'),
]
"""
with open(os.path.join(BASE_DIR, "products", "urls.py"), "w", encoding="utf-8") as f:
    f.write(products_urls)

# products/admin.py
products_admin = """from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'created_at')
    search_fields = ('name', 'business__name')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'category', 'purchase_price', 'selling_price', 'stock_quantity', 'business')
    list_filter = ('category', 'is_imei_tracked', 'business')
    search_fields = ('name', 'brand', 'sku', 'barcode')
"""
with open(os.path.join(BASE_DIR, "products", "admin.py"), "w", encoding="utf-8") as f:
    f.write(products_admin)


# --- 2. INVENTORY & IMEI ---
# inventory/models.py
inventory_models = """from django.db import models
from decimal import Decimal
from core.models import TenantModel

class StockMovement(TenantModel):
    MOVEMENT_TYPES = [
        ('PURCHASE', 'Purchase Received'),
        ('SALE', 'Sale Dispatched'),
        ('RETURN', 'Customer Return'),
        ('ADJUSTMENT', 'Stock Adjustment / Audit'),
    ]
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    previous_stock = models.IntegerField(default=0)
    new_stock = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)
    reference_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Invoice/PO Reference")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.movement_type} ({self.quantity})"

class MobileDevice(TenantModel):
    STATUS_CHOICES = [
        ('IN_STOCK', 'In Stock / Available'),
        ('SOLD', 'Sold / Dispatched'),
        ('RETURNED', 'Returned to Vendor'),
        ('DEFECTIVE', 'Defective / In Repair'),
    ]
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='devices')
    imei_1 = models.CharField(max_length=30, verbose_name="Primary IMEI 1", db_index=True)
    imei_2 = models.CharField(max_length=30, blank=True, null=True, verbose_name="Secondary IMEI 2")
    serial_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Device Serial Number")
    
    model_name = models.CharField(max_length=150, blank=True, null=True, verbose_name="Model / Color / Variant")
    brand = models.CharField(max_length=100, blank=True, null=True)
    
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_STOCK')
    
    customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, null=True, blank=True, related_name='purchased_devices')
    sale_item = models.ForeignKey('sales.SaleItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='device_records')
    sale_date = models.DateTimeField(blank=True, null=True)
    warranty_expiry_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['business', 'imei_1'], name='unique_imei1_per_business')
        ]

    def __str__(self):
        return f"{self.product.name} (IMEI: {self.imei_1}) - {self.status}"
"""
with open(os.path.join(BASE_DIR, "inventory", "models.py"), "w", encoding="utf-8") as f:
    f.write(inventory_models)

# inventory/forms.py
inventory_forms = """from django import forms
from .models import MobileDevice
from products.models import Product

class MobileDeviceForm(forms.ModelForm):
    class Meta:
        model = MobileDevice
        fields = [
            'product', 'imei_1', 'imei_2', 'serial_number',
            'model_name', 'brand', 'purchase_price', 'selling_price', 'status', 'notes'
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'imei_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '15-digit IMEI 1', 'required': True}),
            'imei_2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional IMEI 2'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional S/N'}),
            'model_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 128GB Black'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Apple'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        if business:
            self.fields['product'].queryset = Product.objects.filter(business=business, is_imei_tracked=True)

class BulkIMEIForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.none(), widget=forms.Select(attrs={'class': 'form-select'}))
    imei_list = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Paste list of IMEI numbers, one per line'}),
        help_text="One IMEI number per line."
    )
    purchase_price = forms.DecimalField(widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    selling_price = forms.DecimalField(widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        if business:
            self.fields['product'].queryset = Product.objects.filter(business=business, is_imei_tracked=True)
"""
with open(os.path.join(BASE_DIR, "inventory", "forms.py"), "w", encoding="utf-8") as f:
    f.write(inventory_forms)

# inventory/views.py
inventory_views = """from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from decimal import Decimal
from core.utils import business_required
from .models import StockMovement, MobileDevice
from .forms import MobileDeviceForm, BulkIMEIForm
from products.models import Product

@business_required
def stock_list(request):
    business = request.business
    products = Product.objects.filter(business=business).select_related('category')
    
    total_items = sum(p.stock_quantity for p in products)
    total_val_cost = sum(p.stock_quantity * p.purchase_price for p in products)
    total_val_mrp = sum(p.stock_quantity * p.selling_price for p in products)
    low_stock_count = sum(1 for p in products if p.is_low_stock())
    out_stock_count = sum(1 for p in products if p.is_out_of_stock())
    
    movements = StockMovement.objects.filter(business=business).select_related('product')[:20]
    
    return render(request, 'inventory/stock_list.html', {
        'products': products,
        'total_items': total_items,
        'total_val_cost': total_val_cost,
        'total_val_mrp': total_val_mrp,
        'low_stock_count': low_stock_count,
        'out_stock_count': out_stock_count,
        'recent_movements': movements,
    })

@business_required
def imei_list(request):
    business = request.business
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    
    devices = MobileDevice.objects.filter(business=business).select_related('product', 'customer')
    
    if query:
        devices = devices.filter(
            Q(imei_1__icontains=query) |
            Q(imei_2__icontains=query) |
            Q(serial_number__icontains=query) |
            Q(product__name__icontains=query) |
            Q(customer__name__icontains=query) |
            Q(customer__phone__icontains=query)
        )
        
    if status_filter:
        devices = devices.filter(status=status_filter)
        
    paginator = Paginator(devices, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    in_stock_count = MobileDevice.objects.filter(business=business, status='IN_STOCK').count()
    sold_count = MobileDevice.objects.filter(business=business, status='SOLD').count()
    
    return render(request, 'inventory/imei_list.html', {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'in_stock_count': in_stock_count,
        'sold_count': sold_count,
    })

@business_required
def imei_create(request):
    business = request.business
    if request.method == 'POST':
        form = MobileDeviceForm(request.POST, business=business)
        if form.is_valid():
            device = form.save(commit=False)
            device.business = business
            device.save()
            
            # Update product stock
            if device.status == 'IN_STOCK':
                prod = device.product
                old_stk = prod.stock_quantity
                prod.stock_quantity += 1
                prod.save(update_fields=['stock_quantity'])
                StockMovement.objects.create(
                    business=business,
                    product=prod,
                    movement_type='PURCHASE',
                    quantity=1,
                    previous_stock=old_stk,
                    new_stock=prod.stock_quantity,
                    notes=f"Added device with IMEI: {device.imei_1}"
                )
                
            messages.success(request, f"Device with IMEI {device.imei_1} registered successfully!")
            return redirect('inventory:imei_list')
    else:
        form = MobileDeviceForm(business=business)
        
    return render(request, 'inventory/imei_form.html', {
        'form': form,
        'title': 'Register Mobile Device / IMEI'
    })

@business_required
def imei_search(request):
    \"\"\"Global IMEI Quick Search Tool for instant device lifecycle lookup.\"\"\"
    business = request.business
    query = request.GET.get('imei', '').strip()
    device = None
    if query:
        device = MobileDevice.objects.filter(
            business=business
        ).filter(
            Q(imei_1__iexact=query) | Q(imei_2__iexact=query) | Q(serial_number__iexact=query)
        ).select_related('product', 'customer', 'sale_item__sale').first()
        
    return render(request, 'inventory/imei_search.html', {
        'query': query,
        'device': device,
    })
"""
with open(os.path.join(BASE_DIR, "inventory", "views.py"), "w", encoding="utf-8") as f:
    f.write(inventory_views)

# inventory/urls.py
inventory_urls = """from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('stock/', views.stock_list, name='stock_list'),
    path('imei/', views.imei_list, name='imei_list'),
    path('imei/add/', views.imei_create, name='imei_create'),
    path('imei/search/', views.imei_search, name='imei_search'),
]
"""
with open(os.path.join(BASE_DIR, "inventory", "urls.py"), "w", encoding="utf-8") as f:
    f.write(inventory_urls)

# inventory/admin.py
inventory_admin = """from django.contrib import admin
from .models import StockMovement, MobileDevice

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'movement_type', 'quantity', 'previous_stock', 'new_stock', 'created_at')
    list_filter = ('movement_type', 'business')
    search_fields = ('product__name', 'notes', 'reference_id')

@admin.register(MobileDevice)
class MobileDeviceAdmin(admin.ModelAdmin):
    list_display = ('imei_1', 'product', 'brand', 'status', 'customer', 'selling_price')
    list_filter = ('status', 'brand', 'business')
    search_fields = ('imei_1', 'imei_2', 'serial_number', 'product__name', 'customer__name')
"""
with open(os.path.join(BASE_DIR, "inventory", "admin.py"), "w", encoding="utf-8") as f:
    f.write(inventory_admin)

print("Phase 4 (Products & Inventory) created successfully!")
