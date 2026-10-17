from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from decimal import Decimal
from django.db import transaction
from payments.models import Payment
from payments.services import settle_after_payment
from payments.upi_service import parse_money
from customers.models import Customer
from suppliers.models import Supplier
from core.utils import build_whatsapp_url, format_inr
from api.serializers import PaymentSerializer
from api.permissions import HasActiveBusiness, PaymentsPermission, SuppliersPermission

class PaymentListAPIView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [HasActiveBusiness, PaymentsPermission]

    def get_queryset(self):
        qs = Payment.objects.filter(business=self.request.business).select_related('customer', 'supplier')
        p_type = self.request.query_params.get('type')
        if p_type:
            qs = qs.filter(payment_type=p_type)
        return qs

class CustomerPaymentCreateAPIView(APIView):
    permission_classes = [HasActiveBusiness, PaymentsPermission]

    def post(self, request):
        business = request.business
        customer_id = request.data.get('customer_id')
        # parse_money is a strict, float-free money parser: it quantizes to
        # two decimals, so a client float like 0.30000000000000004 can never
        # slip past the overpayment guard below.
        amount = parse_money(request.data.get('amount'))
        method = request.data.get('payment_method', 'CASH')
        date = request.data.get('payment_date')
        ref = request.data.get('reference_number', '')
        notes = request.data.get('notes', '')

        if not customer_id or amount is None:
            return Response({'error': 'Valid customer and positive amount are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            customer = Customer.objects.get(pk=customer_id, business=business)

            # Financial integrity: never let the books drift. An overpayment
            # would be swallowed by get_outstanding_due()'s floor at zero and
            # the extra money would vanish from the customer's ledger. The
            # shop must record the actual amount received, within the due.
            outstanding = customer.get_outstanding_due()
            if amount > outstanding:
                return Response({
                    'error': f'Amount ({format_inr(amount)}) exceeds this customer\'s '
                             f'outstanding due ({format_inr(outstanding)}). Record the exact '
                             f'amount received, up to the outstanding balance.'
                }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                payment = Payment.objects.create(
                    business=business,
                    payment_type='CUSTOMER_PAYMENT',
                    customer=customer,
                    amount=amount,
                    payment_method=method,
                    payment_date=date or timezone.now().date(),
                    reference_number=ref,
                    notes=notes
                )
                # Recompute the per-invoice settlement (paid / due / status)
                # so bills never disagree with the books again.
                settlements = settle_after_payment(customer)

            customer.refresh_from_db()
            rem_due = customer.get_outstanding_due()
            wa_msg = f"Namaste {customer.name},\n\nWe have received your payment of *{format_inr(amount)}*.\nRemaining Khata Balance: *{format_inr(rem_due)}*.\n\nThank you for shopping at *{business.name}*!"
            wa_url = build_whatsapp_url(customer.phone, wa_msg)

            return Response({
                'message': 'Payment recorded successfully.',
                'payment': PaymentSerializer(payment).data,
                'remaining_due': float(rem_due),
                'settled_invoices': settlements,
                'whatsapp_receipt_url': wa_url,
            }, status=status.HTTP_201_CREATED)

        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)

class SupplierPaymentCreateAPIView(APIView):
    # Supplier payments reveal supplier cost/ledger details — owner (or a
    # staff member explicitly granted both payments AND suppliers) only.
    permission_classes = [HasActiveBusiness, PaymentsPermission, SuppliersPermission]

    def post(self, request):
        business = request.business
        supplier_id = request.data.get('supplier_id')
        amount = Decimal(str(request.data.get('amount', '0') or '0'))
        method = request.data.get('payment_method', 'CASH')
        date = request.data.get('payment_date')
        ref = request.data.get('reference_number', '')
        notes = request.data.get('notes', '')

        if not supplier_id or amount <= 0:
            return Response({'error': 'Valid supplier and positive amount are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            supplier = Supplier.objects.get(pk=supplier_id, business=business)
            payment = Payment.objects.create(
                business=business,
                payment_type='SUPPLIER_PAYMENT',
                supplier=supplier,
                amount=amount,
                payment_method=method,
                payment_date=date or timezone.now().date(),
                reference_number=ref,
                notes=notes
            )

            return Response({
                'message': 'Supplier payment voucher recorded.',
                'payment': PaymentSerializer(payment).data,
                'remaining_due': float(supplier.get_outstanding_due()),
            }, status=status.HTTP_201_CREATED)

        except Supplier.DoesNotExist:
            return Response({'error': 'Supplier not found.'}, status=status.HTTP_404_NOT_FOUND)
