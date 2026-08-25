from django.db import models
from decimal import Decimal
from django.utils import timezone
from core.models import TenantModel

class Payment(TenantModel):
    PAYMENT_TYPES = [
        ('CUSTOMER_PAYMENT', 'Customer Payment / Khata Inflow'),
        ('SUPPLIER_PAYMENT', 'Supplier Payment / Outflow'),
    ]
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('UPI', 'UPI (GPay / PhonePe / Paytm)'),
        ('CARD', 'Card'),
        ('BANK', 'Bank Transfer / NEFT'),
        ('OTHER', 'Other'),
    ]
    payment_type = models.CharField(max_length=25, choices=PAYMENT_TYPES)
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, null=True, blank=True, related_name='payments')
    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.CASCADE, null=True, blank=True, related_name='payments')
    sale = models.ForeignKey('sales.Sale', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    purchase = models.ForeignKey('purchases.Purchase', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Amount (₹)")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    payment_date = models.DateField(default=timezone.now)
    reference_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Txn Ref / UTR / Receipt No.")
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        party = self.customer.name if self.customer else (self.supplier.company_name if self.supplier else "General")
        return f"{self.get_payment_type_display()}: ₹{self.amount} from/to {party}"
