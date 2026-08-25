from django.db import models
from decimal import Decimal
from django.utils import timezone
from core.models import TenantModel

DEFAULT_EXPENSE_CATEGORIES = [
    'Shop Rent',
    'Electricity Bill',
    'Staff Salary',
    'Internet & Telephone',
    'Transport & Delivery',
    'Shop Maintenance & Repairs',
    'Marketing & Ads',
    'Tea & Refreshments',
    'Packaging & Bags',
    'Other Business Expenses'
]

class ExpenseCategory(TenantModel):
    name = models.CharField(max_length=100, verbose_name="Category Name")

    class Meta:
        verbose_name_plural = "Expense Categories"
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['business', 'name'], name='unique_expense_category_per_business')
        ]

    def __str__(self):
        return self.name

class Expense(TenantModel):
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('UPI', 'UPI / Online'),
        ('CARD', 'Card'),
        ('BANK', 'Bank Transfer'),
    ]
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    title = models.CharField(max_length=200, verbose_name="Expense Description / Title")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Amount (₹)")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    expense_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)
    receipt_image = models.ImageField(upload_to='expenses/', blank=True, null=True)

    class Meta:
        ordering = ['-expense_date', '-created_at']

    def __str__(self):
        return f"{self.title} - ₹{self.amount} ({self.expense_date})"
