from django.db import models
from decimal import Decimal
from core.models import TenantModel
from core.utils import build_whatsapp_url, format_inr

class Customer(TenantModel):
    name = models.CharField(max_length=150, verbose_name="Customer Name")
    phone = models.CharField(max_length=15, verbose_name="Mobile / WhatsApp Number", db_index=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True, verbose_name="Address")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes / Khata Remarks")
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Credit Limit (₹)")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.phone})"

    def get_total_sales(self):
        total = self.sales.aggregate(models.Sum('total_amount'))['total_amount__sum']
        return total or Decimal('0.00')

    def get_total_paid(self):
        # Payments directly attached to customer
        total_payments = self.payments.filter(payment_type='CUSTOMER_PAYMENT').aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0.00')
        return total_payments

    def get_outstanding_due(self):
        total_sales = self.get_total_sales()
        total_paid = self.get_total_paid()
        due = total_sales - total_paid
        return max(Decimal('0.00'), due)

    def get_whatsapp_reminder_url(self):
        due = self.get_outstanding_due()
        if due <= 0:
            return ""
        shop_name = self.business.name if self.business else "our shop"
        msg = f"Namaste {self.name},\\n\\nYour outstanding Khata balance with *{shop_name}* is *{format_inr(due)}*.\\n\\nPlease settle the payment at your earliest convenience.\\n\\nThank you!"
        return build_whatsapp_url(self.phone, msg)
