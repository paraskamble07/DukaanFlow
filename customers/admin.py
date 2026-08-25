from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'business', 'credit_limit', 'created_at')
    search_fields = ('name', 'phone', 'email', 'business__name')
    list_filter = ('business', 'created_at')
