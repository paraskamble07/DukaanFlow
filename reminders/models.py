import django.db.models.deletion
from django.conf import settings
from django.db import models

from core.models import TenantModel


class ReminderLog(TenantModel):
    """A shop's payment reminder sent (or attempted) to a customer.

    Reminders are user-confirmed composer actions (WhatsApp / SMS) — the
    app never claims a message was delivered; the log records that the
    shop initiated the reminder. Outstanding amounts are always
    recalcuated on the server before a reminder can be logged, and
    settled balances cannot be reminded at all.
    """

    CHANNELS = [
        ('WHATSAPP', 'WhatsApp'),
        ('SMS', 'SMS'),
        ('OTHER', 'Other'),
    ]

    STATUS = [
        ('OVERDUE', 'Overdue'),
        ('DUE_SOON', 'Due soon'),
        ('DUE', 'Due'),
    ]

    customer = models.ForeignKey(
        'customers.Customer', on_delete=models.CASCADE,
        related_name='reminder_logs',
    )
    sale = models.ForeignKey(
        'sales.Sale', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reminder_logs',
        help_text='The credit sale the reminder refers to (if applicable).',
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    channel = models.CharField(max_length=10, choices=CHANNELS)
    reminder_status = models.CharField(max_length=10, choices=STATUS, default='DUE')
    note = models.TextField(blank=True, default='')
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reminder_logs',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Reminder log'
        verbose_name_plural = 'Reminder logs'

    def __str__(self):
        return f'{self.customer.name} ₹{self.amount} via {self.channel} ({self.created_at:%d-%m-%Y})'


class ReminderSetting(TenantModel):
    """Per-shop reminder defaults: credit period and the soon-due window."""

    credit_days = models.PositiveIntegerField(
        default=30, verbose_name='Default credit period (days)',
        help_text='A credit sale becomes due this many days after its date.',
    )
    due_soon_days = models.PositiveIntegerField(
        default=7, verbose_name='Due-soon window (days)',
        help_text='Balances due within this many days are flagged "due soon".',
    )

    class Meta:
        verbose_name = 'Reminder setting'
        verbose_name_plural = 'Reminder settings'
