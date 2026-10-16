from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from products.models import Product, Category, DEFAULT_CATEGORIES
from inventory.models import StockMovement, MobileDevice
from purchases.models import PurchaseItem
from sales.models import SaleItem
from api.serializers import (ProductSerializer, CategorySerializer,
                             StockMovementSerializer, MobileDeviceSerializer)
from api.permissions import HasActiveBusiness, ProductsPermission

# Same definition as the stock report: no sale in the last 60 days while
# units are still on the shelf (Phase 11). Kept in one place so the report
# and the product list/detail cannot drift apart.
DEAD_STOCK_DAYS = 60


def is_dead_stock(product, last_sale_date):
    if product.stock_quantity <= 0:
        return False
    if last_sale_date is None:
        return True
    cutoff = timezone.now().date() - timedelta(days=DEAD_STOCK_DAYS)
    return last_sale_date.date() <= cutoff

def ensure_default_categories(business):
    for cat_name in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(business=business, name=cat_name)

class CategoryListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [HasActiveBusiness, ProductsPermission]

    def get_queryset(self):
        ensure_default_categories(self.request.business)
        return Category.objects.filter(business=self.request.business)

    def perform_create(self, serializer):
        serializer.save(business=self.request.business)

class ProductListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [HasActiveBusiness, ProductsPermission]

    def get_queryset(self):
        business = self.request.business
        ensure_default_categories(business)
        qs = Product.objects.filter(business=business).select_related('category', 'supplier')

        q = self.request.query_params.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(brand__icontains=q) |
                Q(sku__icontains=q) |
                Q(barcode__icontains=q)
            )

        cat_id = self.request.query_params.get('category')
        if cat_id:
            qs = qs.filter(category_id=cat_id)

        stock_filter = self.request.query_params.get('stock')
        if stock_filter in ('low', 'out', 'in_stock', 'dead'):
            products = list(qs)
            if stock_filter == 'low':
                qs = [p for p in products if p.is_low_stock()]
            elif stock_filter == 'out':
                qs = [p for p in products if p.is_out_of_stock()]
            elif stock_filter == 'in_stock':
                qs = [p for p in products if p.stock_quantity > p.min_stock]
            else:
                # Dead stock must be decided per product from its real last
                # sale date — it can never be read off the product row alone.
                cutoff = timezone.now().date() - timedelta(days=DEAD_STOCK_DAYS)
                qs = [
                    p for p in products
                    if p.stock_quantity > 0 and not SaleItem.objects.filter(
                        product=p, sale__business=self.request.business,
                        sale__sale_date__date__gt=cutoff).exists()
                ]

        return qs

    def create(self, request, *args, **kwargs):
        business = request.business
        can_add, count, limit = business.can_add_product()
        if not can_add:
            return Response({
                'error': f'Free plan limit of {limit} products reached. Please upgrade to Pro for unlimited products.'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save(business=business)

        # Log initial stock movement if stock > 0
        if product.stock_quantity > 0:
            StockMovement.objects.create(
                business=business,
                product=product,
                movement_type='ADJUSTMENT',
                quantity=product.stock_quantity,
                previous_stock=0,
                new_stock=product.stock_quantity,
                notes="Initial stock entered via mobile app"
            )

        return Response(ProductSerializer(product, context={'request': request}).data, status=status.HTTP_201_CREATED)

class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [HasActiveBusiness, ProductsPermission]

    def get_queryset(self):
        return Product.objects.filter(business=self.request.business).select_related('category', 'supplier')

    def retrieve(self, request, *args, **kwargs):
        """Product row plus the Phase 11 history sections: stock movements,
        purchase history, registered IMEI units, and a dead-stock verdict."""
        product = self.get_object()
        business = request.business
        data = ProductSerializer(product, context={'request': request}).data

        movements = StockMovement.objects.filter(
            business=business, product=product
        ).select_related('device')[:15]
        purchase_items = PurchaseItem.objects.filter(
            product=product, purchase__business=business
        ).select_related('purchase', 'purchase__supplier').order_by(
            '-purchase__purchase_date')[:10]
        last_sale = SaleItem.objects.filter(
            product=product, sale__business=business
        ).order_by('-sale__sale_date').first()
        last_sale_date = last_sale.sale.sale_date if last_sale else None

        devices = []
        if product.is_imei_tracked:
            devices = MobileDevice.objects.filter(
                business=business, product=product
            ).select_related('customer')[:10]

        data.update({
            'movements': StockMovementSerializer(movements, many=True).data,
            'purchase_history': [
                {
                    'id': item.pk,
                    'invoice_number': item.purchase.invoice_number,
                    'supplier_name': item.purchase.supplier.company_name if item.purchase.supplier else None,
                    'purchase_date': item.purchase.purchase_date,
                    'quantity': item.quantity,
                    'unit_cost': float(item.unit_cost),
                    'total_cost': float(item.total_cost),
                } for item in purchase_items
            ],
            'devices': MobileDeviceSerializer(devices, many=True).data,
            'last_sale_date': last_sale_date,
            'is_dead_stock': is_dead_stock(product, last_sale_date),
        })
        return Response(data)

    def perform_update(self, serializer):
        old_stock = self.get_object().stock_quantity
        product = serializer.save()

        if product.stock_quantity != old_stock:
            diff = product.stock_quantity - old_stock
            StockMovement.objects.create(
                business=self.request.business,
                product=product,
                movement_type='ADJUSTMENT',
                quantity=abs(diff),
                previous_stock=old_stock,
                new_stock=product.stock_quantity,
                notes=f"Stock updated from {old_stock} to {product.stock_quantity}"
            )
