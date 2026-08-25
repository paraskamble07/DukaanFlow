from django.contrib import admin
from .models import Purchase, PurchaseItem

class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'supplier', 'total_amount', 'paid_amount', 'due_amount', 'purchase_date')
    list_filter = ('payment_method', 'business')
    search_fields = ('invoice_number', 'supplier__company_name')
    inlines = [PurchaseItemInline]
