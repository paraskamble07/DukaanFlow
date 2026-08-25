from django.contrib import admin
from .models import Supplier

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'name', 'phone', 'business')
    search_fields = ('company_name', 'name', 'phone')
