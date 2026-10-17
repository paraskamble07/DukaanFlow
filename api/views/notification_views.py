"""In-app notifications (owner/staff, read-only, fully derived).

Nothing is stored: the feed is recomputed from the live books on every
request, so a notification can never point at stale or hand-entered state.
Each item is actionable — the app deep-links from the item to the screen
that resolves it (Khata list, product catalog).
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone

from api.permissions import HasActiveBusiness
from api.serializers import CustomerSerializer, ProductSerializer
from core.utils import format_inr
from customers.models import Customer
from products.models import Product
from suppliers.models import Supplier


class NotificationsAPIView(APIView):
    """The shop's current attention list.

    Response shape:
      results: [ {id, type, title, body, severity, count, total, items} ]
        - type 'KHATA_DUE'   : customers with an outstanding balance
        - type 'LOW_STOCK'   : products at or below their reorder level
        - type 'SUPPLIER_DUE': suppliers with an outstanding balance
      unread_count: number of item *groups* needing attention
      as_of: ISO timestamp of the snapshot
    """
    permission_classes = [IsAuthenticated, HasActiveBusiness]

    def get(self, request):
        business = request.business
        results = []

        customers = Customer.objects.filter(business=business)
        due_customers = sorted(
            (c for c in customers if c.get_outstanding_due() > 0),
            key=lambda c: -c.get_outstanding_due())
        if due_customers:
            total = sum(c.get_outstanding_due() for c in due_customers)
            results.append({
                'id': 'khata_due',
                'type': 'KHATA_DUE',
                'title': 'Khata payments to collect',
                'body': (
                    f"{len(due_customers)} customer(s) owe you a total of "
                    f"{format_inr(total)}."),
                'severity': 'warning',
                'count': len(due_customers),
                'total': float(total),
                'items': CustomerSerializer(
                    due_customers[:5], many=True,
                    context={'request': request}).data,
            })

        products = Product.objects.filter(business=business)
        low_stock = [p for p in products if p.is_low_stock() or p.is_out_of_stock()]
        if low_stock:
            out_of_stock = [p for p in low_stock if p.is_out_of_stock()]
            results.append({
                'id': 'low_stock',
                'type': 'LOW_STOCK',
                'title': 'Stock needs attention',
                'body': (
                    f"{len(out_of_stock)} product(s) out of stock, "
                    f"{len(low_stock) - len(out_of_stock)} at or below "
                    f"reorder level."),
                'severity': 'warning',
                'count': len(low_stock),
                'items': ProductSerializer(
                    low_stock[:5], many=True,
                    context={'request': request}).data,
            })

        suppliers = Supplier.objects.filter(business=business)
        due_suppliers = [s for s in suppliers if s.get_outstanding_due() > 0]
        if due_suppliers:
            total = sum(s.get_outstanding_due() for s in due_suppliers)
            results.append({
                'id': 'supplier_due',
                'type': 'SUPPLIER_DUE',
                'title': 'Suppliers to pay',
                'body': (
                    f"You owe {format_inr(total)} across "
                    f"{len(due_suppliers)} supplier(s)."),
                'severity': 'info',
                'count': len(due_suppliers),
                'total': float(total),
            })

        return Response({
            'results': results,
            'attention_count': len(results),
            'as_of': timezone.now().isoformat(),
        })
