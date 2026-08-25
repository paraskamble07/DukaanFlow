from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'created_at')
    search_fields = ('name', 'business__name')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'category', 'purchase_price', 'selling_price', 'stock_quantity', 'business')
    list_filter = ('category', 'is_imei_tracked', 'business')
    search_fields = ('name', 'brand', 'sku', 'barcode')
