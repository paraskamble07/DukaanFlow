from django import forms
from .models import MobileDevice
from products.models import Product

class MobileDeviceForm(forms.ModelForm):
    class Meta:
        model = MobileDevice
        fields = [
            'product', 'imei_1', 'imei_2', 'serial_number',
            'model_name', 'brand', 'purchase_price', 'selling_price', 'status', 'notes'
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'imei_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '15-digit IMEI 1', 'required': True}),
            'imei_2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional IMEI 2'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional S/N'}),
            'model_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 128GB Black'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Apple'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        if business:
            self.fields['product'].queryset = Product.objects.filter(business=business, is_imei_tracked=True)

class BulkIMEIForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.none(), widget=forms.Select(attrs={'class': 'form-select'}))
    imei_list = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Paste list of IMEI numbers, one per line'}),
        help_text="One IMEI number per line."
    )
    purchase_price = forms.DecimalField(widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    selling_price = forms.DecimalField(widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        if business:
            self.fields['product'].queryset = Product.objects.filter(business=business, is_imei_tracked=True)
