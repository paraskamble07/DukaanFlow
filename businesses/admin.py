from django.contrib import admin
from .models import Business

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner_name', 'phone', 'city', 'plan_tier', 'created_at')
    list_filter = ('plan_tier', 'state', 'created_at')
    search_fields = ('name', 'owner_name', 'phone', 'email', 'gstin')
