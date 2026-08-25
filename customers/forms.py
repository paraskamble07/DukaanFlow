from django import forms
from .models import Customer

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email', 'address', 'credit_limit', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name', 'required': True}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit mobile number', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Optional email'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Locality, City'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Special notes or references'}),
        }
