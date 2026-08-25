from django.shortcuts import render, redirect, get_object_or_404
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
