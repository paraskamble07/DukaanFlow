from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from inventory.models import StockMovement, MobileDevice
from products.models import Product
from api.serializers import StockMovementSerializer, MobileDeviceSerializer
from api.permissions import HasActiveBusiness

class StockMovementListAPIView(generics.ListAPIView):
    serializer_class = StockMovementSerializer
    permission_classes = [HasActiveBusiness]

    def get_queryset(self):
        qs = StockMovement.objects.filter(business=self.request.business).select_related('product')
        product_id = self.request.query_params.get('product')
        if product_id:
            qs = qs.filter(product_id=product_id)
        return qs

class StockAdjustmentAPIView(APIView):
    permission_classes = [HasActiveBusiness]

    def post(self, request):
        business = request.business
        product_id = request.data.get('product_id')
        action = request.data.get('action')  # 'INCREASE' or 'DECREASE'
        quantity = int(request.data.get('quantity', 1))
        reason = request.data.get('reason', 'Audit Correction')
        notes = request.data.get('notes', '')

        if not product_id or quantity <= 0:
            return Response({'error': 'Valid product and positive quantity required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(pk=product_id, business=business)
            old_stock = product.stock_quantity
            
            if action == 'DECREASE':
                if product.stock_quantity < quantity:
                    return Response({'error': f'Cannot deduct {quantity} units. Current stock is {product.stock_quantity}.'}, status=status.HTTP_400_BAD_REQUEST)
                product.stock_quantity -= quantity
            else:
                product.stock_quantity += quantity
                
            product.save(update_fields=['stock_quantity'])

            movement = StockMovement.objects.create(
                business=business,
                product=product,
                movement_type='ADJUSTMENT',
                quantity=quantity,
                previous_stock=old_stock,
                new_stock=product.stock_quantity,
                notes=f"Stock {action}: {reason} - {notes}".strip(' -')
            )

            return Response({
                'message': f'Stock updated successfully to {product.stock_quantity} units.',
                'product_id': product.id,
                'new_stock': product.stock_quantity,
                'movement': StockMovementSerializer(movement).data
            }, status=status.HTTP_200_OK)

        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

class MobileDeviceListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = MobileDeviceSerializer
    permission_classes = [HasActiveBusiness]

    def get_queryset(self):
        business = self.request.business
        qs = MobileDevice.objects.filter(business=business).select_related('product', 'customer')

        q = self.request.query_params.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(imei_1__icontains=q) |
                Q(imei_2__icontains=q) |
                Q(serial_number__icontains=q) |
                Q(product__name__icontains=q) |
                Q(customer__name__icontains=q)
            )

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs

    def perform_create(self, serializer):
        device = serializer.save(business=self.request.business)
        if device.status == 'IN_STOCK':
            prod = device.product
            old_stk = prod.stock_quantity
            prod.stock_quantity += 1
            prod.save(update_fields=['stock_quantity'])
            StockMovement.objects.create(
                business=self.request.business,
                product=prod,
                movement_type='PURCHASE',
                quantity=1,
                previous_stock=old_stk,
                new_stock=prod.stock_quantity,
                notes=f"Device registered with IMEI: {device.imei_1}"
            )

class IMEILookupAPIView(APIView):
    permission_classes = [HasActiveBusiness]

    def get(self, request):
        imei = request.query_params.get('imei', '').strip()
        if not imei:
            return Response({'error': 'IMEI query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        device = MobileDevice.objects.filter(
            business=request.business
        ).filter(
            Q(imei_1__iexact=imei) | Q(imei_2__iexact=imei) | Q(serial_number__iexact=imei)
        ).select_related('product', 'customer', 'sale_item__sale').first()

        if not device:
            return Response({'found': False, 'message': f'No device found with IMEI {imei}'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'found': True,
            'device': MobileDeviceSerializer(device).data
        })
