from django import forms
from .models import Supplier

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['company_name', 'name', 'phone', 'email', 'address', 'gstin', 'notes']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. National Mobile Distributors', 'required': True}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Rajesh Gupta', 'required': True}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 9820012345', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Optional email'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'City, State'}),
            'gstin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional GSTIN'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
