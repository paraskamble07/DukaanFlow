from django.shortcuts import render, redirect, get_object_or_404
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
    """Global IMEI Quick Search Tool for instant device lifecycle lookup."""
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
