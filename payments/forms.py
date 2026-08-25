from django import forms
from .models import Payment
from customers.models import Customer
from suppliers.models import Supplier

class CustomerPaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['customer', 'amount', 'payment_method', 'payment_date', 'reference_number', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00', 'required': True}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UPI UTR / Cheque No.'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Khata settlement notes'}),
        }

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        if business:
            self.fields['customer'].queryset = Customer.objects.filter(business=business)

class SupplierPaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['supplier', 'amount', 'payment_method', 'payment_date', 'reference_number', 'notes']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00', 'required': True}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bank Ref / Cheque No.'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        if business:
            self.fields['supplier'].queryset = Supplier.objects.filter(business=business)
