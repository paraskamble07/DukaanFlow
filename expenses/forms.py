from django import forms
from .models import Expense, ExpenseCategory

class ExpenseForm(forms.ModelForm):
    category_name = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Or type new category e.g. Office Supplies'})
    )

    class Meta:
        model = Expense
        fields = ['title', 'category', 'amount', 'payment_method', 'expense_date', 'notes', 'receipt_image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. July Shop Rent', 'required': True}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'required': True}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'expense_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional reference or notes'}),
            'receipt_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        if business:
            self.fields['category'].queryset = ExpenseCategory.objects.filter(business=business)
