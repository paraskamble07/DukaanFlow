from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class RegisterForm(forms.Form):
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Rahul Sharma', 'required': True})
    )
    shop_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Sharma Mobile & Electronics', 'required': True})
    )
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 9876543210', 'required': True})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'e.g. rahul@example.com', 'required': True})
    )
    password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Minimum 6 characters', 'required': True})
    )
    confirm_password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Re-enter password', 'required': True})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

class LoginForm(forms.Form):
    email = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email or Username', 'required': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password', 'required': True})
    )

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))
    phone = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = UserProfile
        fields = ['phone']
