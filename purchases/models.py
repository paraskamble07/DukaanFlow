from django.db import models
from decimal import Decimal
from django.utils import timezone
from core.models import TenantModel

class Purchase(TenantModel):
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('UPI', 'UPI / Online'),
        ('BANK', 'Bank Transfer / NEFT'),
        ('CREDIT', 'Supplier Credit (Khata)'),
    ]
    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.CASCADE, related_name='purchases')
    invoice_number = models.CharField(max_length=100, verbose_name="Supplier Bill / Invoice No.")
    purchase_date = models.DateField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-purchase_date', '-created_at']

    def __str__(self):
        return f"PO #{self.invoice_number} - {self.supplier.company_name} (₹{self.total_amount})"
        
    def save(self, *args, **kwargs):
        self.due_amount = max(Decimal('0.00'), self.total_amount - self.paid_amount)
        super().save(*args, **kwargs)

class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='purchase_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_cost = Decimal(str(self.quantity)) * Decimal(str(self.unit_cost))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
