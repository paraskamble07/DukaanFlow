from django import forms
from .models import Product, Category

class ProductForm(forms.ModelForm):
    category_name = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Or type new category e.g. Chargers'})
    )

    class Meta:
        model = Product
        fields = [
            'name', 'brand', 'category', 'sku', 'barcode',
            'purchase_price', 'selling_price', 'stock_quantity', 'min_stock',
            'warranty_months', 'is_imei_tracked', 'supplier', 'image', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Samsung Galaxy A56 5G', 'required': True}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Samsung, Apple, Realme'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional SKU code'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Scan or enter barcode'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'required': True}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'required': True}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'required': True}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-control', 'value': 5}),
            'warranty_months': forms.NumberInput(attrs={'class': 'form-control', 'value': 12}),
            'is_imei_tracked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        if business:
            self.fields['category'].queryset = Category.objects.filter(business=business)
            from suppliers.models import Supplier
            self.fields['supplier'].queryset = Supplier.objects.filter(business=business)
