from django import forms
from .models import Business

class BusinessSettingsForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = [
            'name', 'owner_name', 'phone', 'email', 'address',
            'city', 'state', 'pincode', 'gstin', 'logo',
            'invoice_prefix', 'invoice_footer', 'plan_tier'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'owner_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'required': True}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'gstin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '27AAPFU0939L1ZV'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'invoice_prefix': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_footer': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'plan_tier': forms.Select(attrs={'class': 'form-select'}),
        }
