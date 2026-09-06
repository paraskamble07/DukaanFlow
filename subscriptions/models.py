from django.db import models
from django.conf import settings
from django.utils import timezone


class SubscriptionPaymentRequest(models.Model):
    """A shop owner's ₹30 subscription payment claim — verified manually by the
    ShopZen admin in their own UPI/bank account before Premium is activated."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Verification'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    business = models.ForeignKey(
        'businesses.Business', on_delete=models.CASCADE, related_name='subscription_requests'
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription_requests'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    upi_reference = models.CharField(
        max_length=50, blank=True, default='',
        verbose_name='UTR / UPI reference number'
    )
    note = models.TextField(blank=True, default='')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    # Filled by admin action
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_subscription_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.business.name} ₹{self.amount} {self.status}'

    @property
    def months_purchased(self):
        """Whole months of Premium this request pays for (₹30/month, Decimal-safe)."""
        from decimal import Decimal
        from businesses.models import SHOPZEN_PREMIUM_PRICE
        price = Decimal(str(SHOPZEN_PREMIUM_PRICE))
        if self.amount <= 0:
            return 0
        return int((self.amount / price).to_integral_value(rounding='ROUND_DOWN'))


class AdminAuditLog(models.Model):
    """Audit trail for privileged ShopZen admin actions (approvals/rejections)."""
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    target = models.CharField(max_length=200, blank=True, default='')
    detail = models.TextField(blank=True, default='')
    result = models.CharField(max_length=20, default='OK')
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.admin} {self.action} {self.target} ({self.result})'
