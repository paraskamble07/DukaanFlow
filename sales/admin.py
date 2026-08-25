from django.contrib import admin
from .models import Sale, SaleItem

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'total_amount', 'paid_amount', 'due_amount', 'payment_status', 'sale_date')
    list_filter = ('payment_status', 'payment_method', 'business')
    search_fields = ('invoice_number', 'customer__name', 'customer__phone')
    inlines = [SaleItemInline]
