from django.db import models
from decimal import Decimal
from core.models import TenantModel

class StockMovement(TenantModel):
    MOVEMENT_TYPES = [
        ('PURCHASE', 'Purchase Received'),
        ('SALE', 'Sale Dispatched'),
        ('RETURN', 'Customer Return'),
        ('ADJUSTMENT', 'Stock Adjustment / Audit'),
    ]
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    previous_stock = models.IntegerField(default=0)
    new_stock = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)
    reference_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Invoice/PO Reference")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.movement_type} ({self.quantity})"

class MobileDevice(TenantModel):
    STATUS_CHOICES = [
        ('IN_STOCK', 'In Stock / Available'),
        ('SOLD', 'Sold / Dispatched'),
        ('RETURNED', 'Returned to Vendor'),
        ('DEFECTIVE', 'Defective / In Repair'),
    ]
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='devices')
    imei_1 = models.CharField(max_length=30, verbose_name="Primary IMEI 1", db_index=True)
    imei_2 = models.CharField(max_length=30, blank=True, null=True, verbose_name="Secondary IMEI 2")
    serial_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Device Serial Number")
    
    model_name = models.CharField(max_length=150, blank=True, null=True, verbose_name="Model / Color / Variant")
    brand = models.CharField(max_length=100, blank=True, null=True)
    
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_STOCK')
    
    customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, null=True, blank=True, related_name='purchased_devices')
    sale_item = models.ForeignKey('sales.SaleItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='device_records')
    sale_date = models.DateTimeField(blank=True, null=True)
    warranty_expiry_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['business', 'imei_1'], name='unique_imei1_per_business')
        ]

    def __str__(self):
        return f"{self.product.name} (IMEI: {self.imei_1}) - {self.status}"
