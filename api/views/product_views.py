from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from products.models import Product, Category, DEFAULT_CATEGORIES
from inventory.models import StockMovement
from api.serializers import ProductSerializer, CategorySerializer
from api.permissions import HasActiveBusiness

def ensure_default_categories(business):
    for cat_name in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(business=business, name=cat_name)

class CategoryListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [HasActiveBusiness]

    def get_queryset(self):
        ensure_default_categories(self.request.business)
        return Category.objects.filter(business=self.request.business)

    def perform_create(self, serializer):
        serializer.save(business=self.request.business)

class ProductListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [HasActiveBusiness]

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
        if stock_filter == 'low':
            qs = [p for p in qs if p.is_low_stock()]
        elif stock_filter == 'out':
            qs = [p for p in qs if p.is_out_of_stock()]
        elif stock_filter == 'in_stock':
            qs = [p for p in qs if p.stock_quantity > p.min_stock]

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
    permission_classes = [HasActiveBusiness]

    def get_queryset(self):
        return Product.objects.filter(business=self.request.business).select_related('category', 'supplier')

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
