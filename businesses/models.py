from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

SHOPZEN_PREMIUM_PRICE = 30  # ₹30 / month

PLAN_LIMITS = {
    'SHOPZEN_PREMIUM': {
        'name': 'ShopZen Premium',
        'price': SHOPZEN_PREMIUM_PRICE,
        'max_customers': 999999,
        'max_products': 999999,
        'has_whatsapp': True,
        'has_pdf': True,
        'has_advanced_reports': True,
        'has_cloud_backup': True,
        'has_insights': True,
        'max_staff': 10,
    }
}

def get_default_subscription_end():
    return timezone.now().date() + timedelta(days=30)

class Business(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_businesses')
    name = models.CharField(max_length=200, verbose_name="Shop / Business Name")
    owner_name = models.CharField(max_length=150, verbose_name="Owner Full Name")
    phone = models.CharField(max_length=20, verbose_name="Mobile / WhatsApp Number")
    email = models.EmailField(verbose_name="Business Email")
    address = models.TextField(blank=True, null=True, verbose_name="Shop Address")
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True, default="Maharashtra")
    pincode = models.CharField(max_length=10, blank=True, null=True)
    gstin = models.CharField(max_length=25, blank=True, null=True, verbose_name="GSTIN Number (Optional)")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    invoice_prefix = models.CharField(max_length=10, default="SZ-", verbose_name="Invoice Prefix")
    next_invoice_number = models.PositiveIntegerField(default=1001)
    invoice_footer = models.TextField(
        default="Thank you for your business! Goods once sold are covered under manufacturer warranty. Visit again.",
        verbose_name="Invoice Terms & Footer"
    )
    plan_tier = models.CharField(max_length=30, default='SHOPZEN_PREMIUM')
    
    # Subscription Lifecycle Tracking
    subscription_start_date = models.DateField(default=timezone.now)
    subscription_end_date = models.DateField(default=get_default_subscription_end)
    subscription_status = models.CharField(max_length=20, default='ACTIVE') # ACTIVE, EXPIRING_SOON, EXPIRED
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.owner_name})"

    def get_plan_info(self):
        return PLAN_LIMITS.get('SHOPZEN_PREMIUM')

    def is_subscription_active(self):
        return timezone.now().date() <= self.subscription_end_date

    def days_until_expiry(self):
        delta = self.subscription_end_date - timezone.now().date()
        return max(0, delta.days)

    def can_add_customer(self):
        return True, self.customers_customer_set.count(), 999999

    def can_add_product(self):
        return True, self.products_product_set.count(), 999999

    def generate_next_invoice_number(self):
        num = f"{self.invoice_prefix}{self.next_invoice_number}"
        self.next_invoice_number += 1
        self.save(update_fields=['next_invoice_number'])
        return num
