from django.shortcuts import render, redirect, get_object_or_404
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
