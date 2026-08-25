from django.db import models
from decimal import Decimal
from core.models import TenantModel

DEFAULT_CATEGORIES = [
    'Smartphones',
    'Feature Phones',
    'Chargers',
    'Cables',
    'Earphones',
    'Covers',
    'Tempered Glass',
    'Power Banks',
    'Smart Watches',
    'Other Accessories'
]

class Category(TenantModel):
    name = models.CharField(max_length=100, verbose_name="Category Name")
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['business', 'name'], name='unique_category_per_business')
        ]

    def __str__(self):
        return self.name

class Product(TenantModel):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=200, verbose_name="Product Name")
    brand = models.CharField(max_length=100, blank=True, null=True, verbose_name="Brand / Manufacturer")
    sku = models.CharField(max_length=100, blank=True, null=True, verbose_name="SKU Code")
    barcode = models.CharField(max_length=100, blank=True, null=True, verbose_name="Barcode / EAN")
    
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Purchase Cost (₹)")
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Selling Price / MRP (₹)")
    
    stock_quantity = models.IntegerField(default=0, verbose_name="Current Stock Quantity")
    min_stock = models.IntegerField(default=5, verbose_name="Low Stock Alert Threshold")
    
    warranty_months = models.PositiveIntegerField(default=0, verbose_name="Warranty Period (Months)")
    is_imei_tracked = models.BooleanField(default=False, verbose_name="Track Serial / IMEI Numbers (Mobile Phones)")
    
    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.SET_NULL, null=True, blank=True, related_name='supplied_products')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Product Image")
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['business', 'sku'], name='unique_sku_per_business')
        ]

    def __str__(self):
        brand_str = f"[{self.brand}] " if self.brand else ""
        return f"{brand_str}{self.name} - ₹{self.selling_price}"

    def is_low_stock(self):
        return 0 < self.stock_quantity <= self.min_stock

    def is_out_of_stock(self):
        return self.stock_quantity <= 0

    def get_profit_margin(self):
        if self.selling_price and self.selling_price > 0:
            diff = self.selling_price - self.purchase_price
            return (diff / self.selling_price) * 100
        return 0
