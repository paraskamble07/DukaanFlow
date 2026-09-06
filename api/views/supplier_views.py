from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from suppliers.models import Supplier
from purchases.models import Purchase, PurchaseItem
from products.models import Product
from inventory.models import StockMovement
from payments.models import Payment
from api.serializers import SupplierSerializer, PurchaseSerializer
from api.permissions import HasActiveBusiness

class SupplierListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = SupplierSerializer
    permission_classes = [HasActiveBusiness]

    def get_queryset(self):
        return Supplier.objects.filter(business=self.request.business)

    def perform_create(self, serializer):
        serializer.save(business=self.request.business)

class SupplierDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SupplierSerializer
    permission_classes = [HasActiveBusiness]

    def get_queryset(self):
        return Supplier.objects.filter(business=self.request.business)

class PurchaseListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PurchaseSerializer
    permission_classes = [HasActiveBusiness]

    def get_queryset(self):
        return Purchase.objects.filter(business=self.request.business).select_related('supplier').prefetch_related('items__product')

    def create(self, request, *args, **kwargs):
        business = request.business
        data = request.data

        supplier_id = data.get('supplier_id')
        bill_no = data.get('invoice_number', '').strip()
        purchase_date = data.get('purchase_date')
        payment_method = data.get('payment_method', 'CASH')
        paid_amount = Decimal(str(data.get('paid_amount', '0') or '0'))
        notes = data.get('notes', '')
        items_data = data.get('items', [])

        if not items_data or not supplier_id:
            return Response({'error': 'Supplier and items are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                supplier = Supplier.objects.get(pk=supplier_id, business=business)
                total_purchase_amt = Decimal('0.00')
                items_to_create = []

                for item in items_data:
                    p_obj = Product.objects.get(pk=item['product_id'], business=business)
                    qty = int(item['quantity'])
                    cost = Decimal(str(item['unit_cost']))
                    line_total = Decimal(str(qty)) * cost
                    total_purchase_amt += line_total
                    items_to_create.append((p_obj, qty, cost, line_total))

                purchase = Purchase.objects.create(
                    business=business,
                    supplier=supplier,
                    invoice_number=bill_no or f"BILL-{business.purchases_purchase_set.count() + 101}",
                    purchase_date=purchase_date or timezone.now().date(),
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

                    old_stock = p_obj.stock_quantity
                    p_obj.stock_quantity += qty
                    p_obj.purchase_price = cost
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

                if paid_amount > 0:
                    Payment.objects.create(
                        business=business,
                        payment_type='SUPPLIER_PAYMENT',
                        supplier=supplier,
                        purchase=purchase,
                        amount=paid_amount,
                        payment_method=payment_method if payment_method != 'CREDIT' else 'CASH',
                        payment_date=purchase.purchase_date,
                        reference_number=f"PO-PAY-{purchase.invoice_number}",
                        notes=f"Payment for purchase #{purchase.invoice_number}"
                    )

                return Response(PurchaseSerializer(purchase).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
