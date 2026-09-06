from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from sales.models import Sale, SaleItem
from customers.models import Customer
from products.models import Product
from inventory.models import StockMovement, MobileDevice
from payments.models import Payment
from core.utils import build_whatsapp_url, format_inr
from invoices.pdf_service import generate_invoice_pdf
from api.serializers import SaleSerializer
from api.permissions import HasActiveBusiness

class POSCheckoutAPIView(APIView):
    permission_classes = [HasActiveBusiness]

    def post(self, request):
        business = request.business
        data = request.data

        customer_id = data.get('customer_id')
        # App sends explicit null for walk-in sales — treat null like absent.
        new_cust_name = (data.get('new_customer_name') or '').strip()
        new_cust_phone = (data.get('new_customer_phone') or '').strip()

        items_data = data.get('items', [])
        discount_val = Decimal(str(data.get('discount', '0') or '0'))
        tax_val = Decimal(str(data.get('tax', '0') or '0'))
        paid_val = Decimal(str(data.get('paid_amount', '0') or '0'))
        payment_method = data.get('payment_method') or 'CASH'
        notes = data.get('notes') or ''

        if not items_data:
            return Response({'error': 'Cart is empty. Please add products.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Validate every cart line BEFORE writing anything so a rejected
            # line can never leave a half-committed bill behind.
            subtotal = Decimal('0.00')
            processed_items = []
            for item in items_data:
                try:
                    p_id = item.get('product_id')
                    qty = int(item.get('quantity', 1))
                    price = Decimal(str(item.get('unit_price')))
                    item_disc = Decimal(str(item.get('discount', '0') or '0'))
                    device_id = item.get('device_id')
                except (TypeError, ArithmeticError):
                    return Response(
                        {'error': 'Invalid item data in cart. Please review the bill and try again.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                product = Product.objects.get(pk=p_id, business=business)
                if product.stock_quantity < qty:
                    return Response({
                        'error': f"Insufficient stock for '{product.name}'. Available: {product.stock_quantity}, Requested: {qty}"
                    }, status=status.HTTP_400_BAD_REQUEST)

                line_total = (price * Decimal(str(qty))) - item_disc
                subtotal += line_total
                processed_items.append((product, qty, price, item_disc, line_total, device_id))

            with transaction.atomic():
                if customer_id:
                    customer = Customer.objects.get(pk=customer_id, business=business)
                elif new_cust_name and new_cust_phone:
                    customer = Customer.objects.create(
                        business=business,
                        name=new_cust_name,
                        phone=new_cust_phone
                    )
                else:
                    customer, _ = Customer.objects.get_or_create(
                        business=business,
                        phone='0000000000',
                        defaults={'name': 'Walk-in / Cash Customer'}
                    )

                total_amt = max(Decimal('0.00'), (subtotal - discount_val) + tax_val)
                paid_amt = min(total_amt, paid_val) if payment_method != 'CREDIT' else Decimal('0.00')
                if payment_method in ['CASH', 'UPI', 'CARD', 'BANK'] and paid_val == Decimal('0.00'):
                    paid_amt = total_amt

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
                        notes=f"Sold to {customer.name} (Bill #{sale.invoice_number})",
                        reference_id=sale.invoice_number
                    )

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

                # WhatsApp Link
                wa_msg = f"Namaste {customer.name},\n\nHere is your invoice *#{sale.invoice_number}* from *{business.name}*:\n"
                wa_msg += f"Total: *{format_inr(sale.total_amount)}*\nPaid: *{format_inr(sale.paid_amount)}*\n"
                if sale.due_amount > 0:
                    wa_msg += f"Due: *{format_inr(sale.due_amount)}*\n"
                wa_msg += f"Date: {sale.sale_date.strftime('%d-%m-%Y')}\n\nThank you for shopping with us!"
                wa_url = build_whatsapp_url(customer.phone, wa_msg)

                return Response({
                    'message': 'Sale completed successfully!',
                    'sale': SaleSerializer(sale).data,
                    'whatsapp_share_url': wa_url,
                }, status=status.HTTP_201_CREATED)

        except Product.DoesNotExist:
            return Response(
                {'error': 'One of the products in the cart was not found in your shop inventory.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Selected customer was not found in your shop records.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            # Log the real cause server-side; the client only gets a safe message.
            import logging, traceback
            logging.getLogger('shopzen.pos').error(
                'Checkout failed for business %s: %s',
                business.id, traceback.format_exc()
            )
            return Response(
                {'error': 'Checkout failed. Nothing was saved — please verify the cart and try again.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

class SaleListAPIView(generics.ListAPIView):
    serializer_class = SaleSerializer
    permission_classes = [HasActiveBusiness]

    def get_queryset(self):
        qs = Sale.objects.filter(business=self.request.business).select_related('customer').prefetch_related('items__product')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(payment_status=status_filter)
        start_date = self.request.query_params.get('start_date')
        if start_date:
            # Treat client dates as shop-local (IST) calendar days.
            tz = timezone.get_current_timezone()
            from datetime import datetime as _dt
            s = _dt.strptime(start_date, '%Y-%m-%d')
            qs = qs.filter(sale_date__gte=_dt(s.year, s.month, s.day, tzinfo=tz))
        end_date = self.request.query_params.get('end_date')
        if end_date:
            tz = timezone.get_current_timezone()
            from datetime import datetime as _dt
            e = _dt.strptime(end_date, '%Y-%m-%d')
            qs = qs.filter(sale_date__lt=_dt(e.year, e.month, e.day, tzinfo=tz) + timezone.timedelta(days=1))
        q = self.request.query_params.get('q', '').strip()
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(invoice_number__icontains=q) |
                Q(customer__name__icontains=q) |
                Q(customer__phone__icontains=q)
            )
        return qs

class SaleDetailAPIView(generics.RetrieveAPIView):
    serializer_class = SaleSerializer
    permission_classes = [HasActiveBusiness]

    def get_queryset(self):
        return Sale.objects.filter(business=self.request.business).select_related('customer').prefetch_related('items__product')
