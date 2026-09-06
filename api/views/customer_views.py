from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from customers.models import Customer
from sales.models import Sale
from payments.models import Payment
from api.serializers import CustomerSerializer, SaleSerializer, PaymentSerializer
from api.permissions import HasActiveBusiness

class CustomerListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [HasActiveBusiness]

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
        customer = serializer.save(business=business)
        return Response(CustomerSerializer(customer).data, status=status.HTTP_201_CREATED)

class CustomerDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [HasActiveBusiness]

    def get_queryset(self):
        return Customer.objects.filter(business=self.request.business)

class CustomerLedgerAPIView(APIView):
    permission_classes = [HasActiveBusiness]

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
