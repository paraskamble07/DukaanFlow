from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from django.http import HttpResponse
from datetime import datetime
from decimal import Decimal
from customers.models import Customer
from sales.models import Sale
from payments.models import Payment
from api.serializers import CustomerSerializer, SaleSerializer, PaymentSerializer
from api.permissions import HasActiveBusiness, CustomersPermission
from core.utils import find_duplicate_customer
from invoices.pdf_service import generate_ledger_pdf
from payments.upi_service import (
    build_upi_uri, clean_upi_id, parse_money, upi_qr_png_base64,
)

class CustomerListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [HasActiveBusiness, CustomersPermission]

    def get_queryset(self):
        business = self.request.business
        qs = Customer.objects.filter(business=business)

        q = self.request.query_params.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(phone__icontains=q) |
                Q(address__icontains=q)
            )

        due_filter = self.request.query_params.get('due')
        if due_filter == 'yes':
            qs = [c for c in qs if c.get_outstanding_due() > 0]
        elif due_filter == 'cleared':
            qs = [c for c in qs if c.get_outstanding_due() <= 0]

        return qs

    def create(self, request, *args, **kwargs):
        business = request.business
        can_add, count, limit = business.can_add_customer()
        if not can_add:
            return Response({
                'error': f'Free plan limit of {limit} customers reached. Please upgrade to Pro for unlimited customers.'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Duplicate prevention: a customer with the same real mobile number
        # already exists in this shop -> point the caller at it instead of
        # forking a second ledger. 409 (not 400) so the app can distinguish
        # "already exists, offer to open it" from a validation error.
        existing = find_duplicate_customer(business, request.data.get('phone'))
        if existing is not None:
            return Response({
                'error': 'A customer with this mobile number already exists in your shop.',
                'code': 'DUPLICATE_CUSTOMER',
                'existing_customer': CustomerSerializer(existing).data,
            }, status=status.HTTP_409_CONFLICT)

        customer = serializer.save(business=business)
        return Response(CustomerSerializer(customer).data, status=status.HTTP_201_CREATED)

class CustomerDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [HasActiveBusiness, CustomersPermission]

    def get_queryset(self):
        return Customer.objects.filter(business=self.request.business)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        existing = find_duplicate_customer(
            request.business, request.data.get('phone', instance.phone),
            exclude_id=instance.id)
        if existing is not None:
            return Response({
                'error': 'Another customer with this mobile number already exists in your shop.',
                'code': 'DUPLICATE_CUSTOMER',
                'existing_customer': CustomerSerializer(existing).data,
            }, status=status.HTTP_409_CONFLICT)
        return super().update(request, *args, **kwargs)

class CustomerLedgerAPIView(APIView):
    permission_classes = [HasActiveBusiness, CustomersPermission]

    def get(self, request, pk):
        try:
            customer = Customer.objects.get(pk=pk, business=request.business)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)

        sales = Sale.objects.filter(customer=customer, business=request.business).order_by('-sale_date')
        payments = Payment.objects.filter(customer=customer, business=request.business).order_by('-payment_date')

        return Response({
            'customer': CustomerSerializer(customer).data,
            'summary': {
                'total_sales': float(customer.get_total_sales()),
                'total_paid': float(customer.get_total_paid()),
                'outstanding_due': float(customer.get_outstanding_due()),
                'whatsapp_reminder_url': customer.get_whatsapp_reminder_url(),
            },
            'sales': SaleSerializer(sales, many=True).data,
            'payments': PaymentSerializer(payments, many=True).data,
        })


class CustomerLedgerPdfAPIView(APIView):
    """Returns the customer's ledger (Khata) statement as a PDF.

    All amounts are recalculated server-side from recorded invoices and
    payments; the PDF is generated on the server so the client can never
    author its own financial totals. Supports optional ?from_date= and
    ?to_date= (YYYY-MM-DD) filters with an opening-balance carry-forward.
    """

    permission_classes = [HasActiveBusiness, CustomersPermission]

    def get(self, request, pk):
        try:
            customer = Customer.objects.get(pk=pk, business=request.business)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)

        def _parse_date(raw, field):
            if raw is None or str(raw).strip() == '':
                return None
            try:
                return datetime.strptime(str(raw).strip(), '%Y-%m-%d').date()
            except ValueError:
                return 'INVALID'

        from_date = _parse_date(request.query_params.get('from_date'), 'from_date')
        to_date = _parse_date(request.query_params.get('to_date'), 'to_date')
        if from_date == 'INVALID' or to_date == 'INVALID':
            return Response({
                'error': 'Invalid date format. Use YYYY-MM-DD.'
            }, status=status.HTTP_400_BAD_REQUEST)
        if from_date and to_date and from_date > to_date:
            return Response({
                'error': 'from_date cannot be after to_date.'
            }, status=status.HTTP_400_BAD_REQUEST)

        pdf_buffer = generate_ledger_pdf(customer, from_date, to_date)
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = \
            'inline; filename="Ledger_%s.pdf"' % customer.name.replace(' ', '_')
        return response


class CustomerUpiQrAPIView(APIView):
    """Server-computed UPI collect QR for a customer's khata outstanding.

    Scanning this QR only opens the customer's UPI app with a pre-filled
    collect request — it is **never** treated as a payment. A payment enters
    the books only when an authorized shop user records it manually via
    POST /api/payments/customer/, which re-validates the amount server-side.
    """

    permission_classes = [HasActiveBusiness, CustomersPermission]

    def get(self, request, pk):
        try:
            customer = Customer.objects.get(pk=pk, business=request.business)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)

        business = request.business
        upi_id = clean_upi_id(business.upi_id)
        if not upi_id:
            return Response({
                'error': 'No UPI ID configured for this shop. The owner can set one '
                         'from Profile / Shop Settings (upi_id field).'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Default collect amount: the current outstanding, recomputed now.
        outstanding = customer.get_outstanding_due()

        custom_amount = request.query_params.get('amount')
        if custom_amount is not None and str(custom_amount).strip() != '':
            override = parse_money(custom_amount)
            if override is None:
                return Response({
                    'error': 'Invalid amount. Use a positive number with up to two decimals.'
                }, status=status.HTTP_400_BAD_REQUEST)
            amount = override
            amount_source = 'custom'
        else:
            amount = outstanding
            amount_source = 'outstanding'

        note = 'Khata payment - %s - %s' % (customer.name, business.name)
        uri = build_upi_uri(upi_id, business.name, amount, note)

        return Response({
            'upi_id': upi_id,
            'payee_name': business.name,
            'customer_id': customer.id,
            'customer_name': customer.name,
            'amount': str(amount.quantize(Decimal('0.00'))),
            'amount_source': amount_source,
            'currency': 'INR',
            'note': note,
            'upi_uri': uri,
            'qr_png_base64': upi_qr_png_base64(uri),
            'confirmed': False,  # a scan is never a confirmation
        })
