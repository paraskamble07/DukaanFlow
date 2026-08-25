from django.contrib import admin
from .models import StockMovement, MobileDevice

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'movement_type', 'quantity', 'previous_stock', 'new_stock', 'created_at')
    list_filter = ('movement_type', 'business')
    search_fields = ('product__name', 'notes', 'reference_id')

@admin.register(MobileDevice)
class MobileDeviceAdmin(admin.ModelAdmin):
    list_display = ('imei_1', 'product', 'brand', 'status', 'customer', 'selling_price')
    list_filter = ('status', 'brand', 'business')
    search_fields = ('imei_1', 'imei_2', 'serial_number', 'product__name', 'customer__name')
