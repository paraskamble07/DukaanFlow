from django.db import models
from decimal import Decimal
from core.models import TenantModel

class Supplier(TenantModel):
    name = models.CharField(max_length=150, verbose_name="Contact Person Name")
    company_name = models.CharField(max_length=200, verbose_name="Distributor / Company Name")
    phone = models.CharField(max_length=20, verbose_name="Phone Number")
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    gstin = models.CharField(max_length=25, blank=True, null=True, verbose_name="Supplier GSTIN")
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['company_name', 'name']

    def __str__(self):
        return f"{self.company_name} ({self.name})"

    def get_total_purchases(self):
        total = self.purchases_purchase_set.aggregate(models.Sum('total_amount'))['total_amount__sum']
        return total or Decimal('0.00')

    def get_total_paid(self):
        total = self.payments_payment_set.aggregate(models.Sum('amount'))['amount__sum']
        return total or Decimal('0.00')

    def get_outstanding_due(self):
        total_purchases = self.get_total_purchases()
        total_paid = self.get_total_paid()
        return max(Decimal('0.00'), total_purchases - total_paid)
