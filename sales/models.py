from django.db import models
from decimal import Decimal
from django.utils import timezone
from core.models import TenantModel

class Sale(TenantModel):
    PAYMENT_STATUS_CHOICES = [
        ('PAID', 'Fully Paid'),
        ('PARTIAL', 'Partially Paid (Khata)'),
        ('UNPAID', 'Credit / Unpaid'),
    ]
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('UPI', 'UPI (GPay / PhonePe / Paytm)'),
        ('CARD', 'Debit / Credit Card'),
        ('BANK', 'Net Banking / Transfer'),
        ('CREDIT', 'Customer Khata / Credit'),
    ]
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='sales')
    invoice_number = models.CharField(max_length=50, verbose_name="Invoice Number", db_index=True)
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="GST Amount (₹)")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PAID')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    
    sale_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-sale_date', '-created_at']
        constraints = [
            models.UniqueConstraint(fields=['business', 'invoice_number'], name='unique_invoice_per_business')
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name} (₹{self.total_amount})"

    def save(self, *args, **kwargs):
        self.due_amount = max(Decimal('0.00'), self.total_amount - self.paid_amount)
        if self.paid_amount >= self.total_amount:
            self.payment_status = 'PAID'
        elif self.paid_amount > 0:
            self.payment_status = 'PARTIAL'
        else:
            self.payment_status = 'UNPAID'
        super().save(*args, **kwargs)

    def get_cogs(self):
        """Calculates Cost of Goods Sold for this sale."""
        cogs = Decimal('0.00')
        for item in self.items.select_related('product'):
            cost = item.product.purchase_price
            cogs += cost * Decimal(str(item.quantity))
        return cogs

    def get_gross_profit(self):
        return self.total_amount - self.get_cogs()

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='sale_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    imei_numbers = models.CharField(max_length=255, blank=True, null=True, verbose_name="IMEI / Serial Numbers")

    def save(self, *args, **kwargs):
        line_sub = (Decimal(str(self.unit_price)) * Decimal(str(self.quantity))) - Decimal(str(self.discount))
        self.total_price = max(Decimal('0.00'), line_sub)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
