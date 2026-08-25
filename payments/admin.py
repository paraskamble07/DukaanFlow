from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_type', 'amount', 'payment_method', 'customer', 'supplier', 'payment_date', 'business')
    list_filter = ('payment_type', 'payment_method', 'payment_date', 'business')
    search_fields = ('customer__name', 'supplier__company_name', 'reference_number')
