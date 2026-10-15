from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('OWNER', 'Shop Owner'),
        ('STAFF', 'Staff Member'),
        ('SHOPZEN_ADMIN', 'ShopZen Admin'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    business = models.ForeignKey('businesses.Business', on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_members')
    phone = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='OWNER')
    # Per-module grants for STAFF. Empty = no modules (most restrictive default).
    # Modules: products, inventory, suppliers, purchases, sales, customers,
    # payments, expenses, reports, settings, whatsapp, sms
    permissions = models.JSONField(default=list, blank=True)
    # Password-reset flow: single-use token issued by the forgot-password
    # endpoint and consumed by the reset-password endpoint. Always stored
    # hashed so a database leak does not expose usable credentials.
    reset_password_token = models.CharField(max_length=128, blank=True, default='')
    reset_password_expires = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"
