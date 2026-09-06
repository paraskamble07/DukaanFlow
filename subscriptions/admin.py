from django.contrib import admin
from .models import SubscriptionPaymentRequest, AdminAuditLog


@admin.register(SubscriptionPaymentRequest)
class SubscriptionPaymentRequestAdmin(admin.ModelAdmin):
    list_display = ('business', 'amount', 'upi_reference', 'status', 'created_at', 'reviewed_by')
    list_filter = ('status',)
    search_fields = ('business__name', 'upi_reference', 'requested_by__email')
    readonly_fields = ('created_at', 'reviewed_at')


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    list_display = ('admin', 'action', 'target', 'result', 'timestamp')
    list_filter = ('action', 'result')
    search_fields = ('admin__username', 'target', 'detail')
    readonly_fields = ('timestamp',)
