from django.contrib import admin

from .models import ReminderLog, ReminderSetting


@admin.register(ReminderLog)
class ReminderLogAdmin(admin.ModelAdmin):
    list_display = ('customer', 'business', 'amount', 'channel', 'reminder_status', 'created_at')
    list_filter = ('channel', 'reminder_status')
    search_fields = ('customer__name', 'customer__phone', 'note')
    ordering = ('-created_at',)


@admin.register(ReminderSetting)
class ReminderSettingAdmin(admin.ModelAdmin):
    list_display = ('business', 'credit_days', 'due_soon_days')
