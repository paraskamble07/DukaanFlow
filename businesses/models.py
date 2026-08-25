from django.db import models
from django.contrib.auth.models import User

PLAN_LIMITS = {
    'FREE': {
        'max_customers': 50,
        'max_products': 100,
        'has_whatsapp': True,
        'has_pdf': True,
        'has_advanced_reports': False,
        'max_staff': 1,
        'name': 'Free Starter',
        'price': 0,
    },
    'PRO': {
        'max_customers': 999999,
        'max_products': 999999,
        'has_whatsapp': True,
        'has_pdf': True,
        'has_advanced_reports': True,
        'max_staff': 3,
        'name': 'Pro Merchant',
        'price': 199,
    },
    'BUSINESS': {
        'max_customers': 999999,
        'max_products': 999999,
        'has_whatsapp': True,
        'has_pdf': True,
        'has_advanced_reports': True,
        'max_staff': 10,
        'name': 'Business Ultra',
        'price': 499,
    }
}

class Business(models.Model):
    PLAN_CHOICES = [
        ('FREE', 'Free Starter (₹0/mo)'),
        ('PRO', 'Pro Merchant (₹199/mo)'),
        ('BUSINESS', 'Business Ultra (₹499/mo)'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_businesses')
    name = models.CharField(max_length=200, verbose_name="Business/Shop Name")
    owner_name = models.CharField(max_length=150, verbose_name="Owner Full Name")
    phone = models.CharField(max_length=20, verbose_name="Mobile Number")
    email = models.EmailField(verbose_name="Business Email")
    address = models.TextField(blank=True, null=True, verbose_name="Shop Address")
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True, default="Maharashtra")
    pincode = models.CharField(max_length=10, blank=True, null=True)
    gstin = models.CharField(max_length=25, blank=True, null=True, verbose_name="GSTIN Number (Optional)")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    invoice_prefix = models.CharField(max_length=10, default="INV-", verbose_name="Invoice Prefix")
    next_invoice_number = models.PositiveIntegerField(default=1001)
    invoice_footer = models.TextField(
        default="Thank you for your business! Goods once sold will be covered under manufacturer warranty. Visit again.",
        verbose_name="Invoice Terms & Footer"
    )
    plan_tier = models.CharField(max_length=20, choices=PLAN_CHOICES, default='FREE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.owner_name})"

    def get_plan_info(self):
        return PLAN_LIMITS.get(self.plan_tier, PLAN_LIMITS['FREE'])

    def can_add_customer(self):
        limits = self.get_plan_info()
        count = self.customers_customer_set.count()
        return count < limits['max_customers'], count, limits['max_customers']

    def can_add_product(self):
        limits = self.get_plan_info()
        count = self.products_product_set.count()
        return count < limits['max_products'], count, limits['max_products']

    def generate_next_invoice_number(self):
        num = f"{self.invoice_prefix}{self.next_invoice_number}"
        self.next_invoice_number += 1
        self.save(update_fields=['next_invoice_number'])
        return num
