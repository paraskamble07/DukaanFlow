from django.contrib import admin
from .models import ExpenseCategory, Expense

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'business')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'amount', 'payment_method', 'expense_date', 'business')
    list_filter = ('category', 'payment_method', 'expense_date', 'business')
    search_fields = ('title', 'notes')
