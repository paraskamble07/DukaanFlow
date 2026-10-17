from django import forms
from .models import Customer
from core.utils import find_duplicate_customer


class CustomerForm(forms.ModelForm):
    # business is optional: views that know the shop pass it in so the
    # duplicate check can run here too; without it the check is skipped.
    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.business = business

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

    def clean_phone(self):
        phone = (self.cleaned_data.get('phone') or '').strip()
        if not phone:
            return phone
        digits = ''.join(ch for ch in phone if ch.isdigit())
        if len(digits) < 10:
            raise forms.ValidationError(
                "Enter a valid mobile number (at least 10 digits).")
        if self.business is not None:
            duplicate = find_duplicate_customer(
                self.business, phone,
                exclude_id=self.instance.pk if self.instance and self.instance.pk else None)
            if duplicate is not None:
                raise forms.ValidationError(
                    f"A customer with this mobile number already exists: "
                    f"{duplicate.name} (added {duplicate.created_at:%d %b %Y}). "
                    f"Open that customer instead of creating a duplicate.")
        return phone
