import json
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
    """Atomic POS checkout handler."""
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
