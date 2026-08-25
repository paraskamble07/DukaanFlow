import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# --- 1. ACCOUNTS ---
# accounts/models.py
accounts_models = """from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('OWNER', 'Shop Owner'),
        ('STAFF', 'Staff Member'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    business = models.ForeignKey('businesses.Business', on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_members')
    phone = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='OWNER')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"
"""
with open(os.path.join(BASE_DIR, "accounts", "models.py"), "w", encoding="utf-8") as f:
    f.write(accounts_models)

# accounts/forms.py
accounts_forms = """from django import forms
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
"""
with open(os.path.join(BASE_DIR, "accounts", "forms.py"), "w", encoding="utf-8") as f:
    f.write(accounts_forms)

# accounts/views.py
accounts_views = """from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, LoginForm, UserProfileForm
from .models import UserProfile
from businesses.models import Business

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            full_name = form.cleaned_data['full_name']
            shop_name = form.cleaned_data['shop_name']
            phone = form.cleaned_data['phone']
            
            # Create User
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=full_name
            )
            
            # Create Business
            business = Business.objects.create(
                owner=user,
                name=shop_name,
                owner_name=full_name,
                phone=phone,
                email=email,
                plan_tier='FREE'
            )
            
            # Create UserProfile
            UserProfile.objects.create(
                user=user,
                business=business,
                phone=phone,
                role='OWNER'
            )
            
            # Auto login
            login(request, user)
            messages.success(request, f"Welcome to DukaanFlow, {full_name}! Your shop '{shop_name}' is now ready.")
            return redirect('dashboard:index')
    else:
        form = RegisterForm()
        
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            user = authenticate(request, username=username_or_email, password=password)
            if user is None and '@' in username_or_email:
                user_obj = User.objects.filter(email__iexact=username_or_email).first()
                if user_obj:
                    user = authenticate(request, username=user_obj.username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get('next', 'dashboard:index')
                return redirect(next_url)
            else:
                messages.error(request, "Invalid email/username or password. Please try again.")
    else:
        form = LoginForm()
        
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('landing:home')

@login_required
def profile_view(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.save()
        
        profile.phone = request.POST.get('phone', profile.phone)
        profile.save()
        
        messages.success(request, "Profile details updated successfully.")
        return redirect('accounts:profile')
        
    return render(request, 'accounts/profile.html', {'user': user, 'profile': profile})
"""
with open(os.path.join(BASE_DIR, "accounts", "views.py"), "w", encoding="utf-8") as f:
    f.write(accounts_views)

# accounts/urls.py
accounts_urls = """from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
]
"""
with open(os.path.join(BASE_DIR, "accounts", "urls.py"), "w", encoding="utf-8") as f:
    f.write(accounts_urls)

# accounts/admin.py
accounts_admin = """from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'business', 'phone', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone')
"""
with open(os.path.join(BASE_DIR, "accounts", "admin.py"), "w", encoding="utf-8") as f:
    f.write(accounts_admin)


# --- 2. BUSINESSES ---
# businesses/models.py
businesses_models = """from django.db import models
from django.contrib.auth.models import User

PLAN_LIMITS = {
    'FREE': {
        'max_customers': 50,
        'max_products': 100,
        'has_whatsapp': True,
        'has_pdf': True,
        'has_advanced_reports': False,
        'max_staff': 1,
        'name': 'Free Starter',
        'price': 0,
    },
    'PRO': {
        'max_customers': 999999,
        'max_products': 999999,
        'has_whatsapp': True,
        'has_pdf': True,
        'has_advanced_reports': True,
        'max_staff': 3,
        'name': 'Pro Merchant',
        'price': 199,
    },
    'BUSINESS': {
        'max_customers': 999999,
        'max_products': 999999,
        'has_whatsapp': True,
        'has_pdf': True,
        'has_advanced_reports': True,
        'max_staff': 10,
        'name': 'Business Ultra',
        'price': 499,
    }
}

class Business(models.Model):
    PLAN_CHOICES = [
        ('FREE', 'Free Starter (₹0/mo)'),
        ('PRO', 'Pro Merchant (₹199/mo)'),
        ('BUSINESS', 'Business Ultra (₹499/mo)'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_businesses')
    name = models.CharField(max_length=200, verbose_name="Business/Shop Name")
    owner_name = models.CharField(max_length=150, verbose_name="Owner Full Name")
    phone = models.CharField(max_length=20, verbose_name="Mobile Number")
    email = models.EmailField(verbose_name="Business Email")
    address = models.TextField(blank=True, null=True, verbose_name="Shop Address")
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True, default="Maharashtra")
    pincode = models.CharField(max_length=10, blank=True, null=True)
    gstin = models.CharField(max_length=25, blank=True, null=True, verbose_name="GSTIN Number (Optional)")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    invoice_prefix = models.CharField(max_length=10, default="INV-", verbose_name="Invoice Prefix")
    next_invoice_number = models.PositiveIntegerField(default=1001)
    invoice_footer = models.TextField(
        default="Thank you for your business! Goods once sold will be covered under manufacturer warranty. Visit again.",
        verbose_name="Invoice Terms & Footer"
    )
    plan_tier = models.CharField(max_length=20, choices=PLAN_CHOICES, default='FREE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.owner_name})"

    def get_plan_info(self):
        return PLAN_LIMITS.get(self.plan_tier, PLAN_LIMITS['FREE'])

    def can_add_customer(self):
        limits = self.get_plan_info()
        count = self.customers_customer_set.count()
        return count < limits['max_customers'], count, limits['max_customers']

    def can_add_product(self):
        limits = self.get_plan_info()
        count = self.products_product_set.count()
        return count < limits['max_products'], count, limits['max_products']

    def generate_next_invoice_number(self):
        num = f"{self.invoice_prefix}{self.next_invoice_number}"
        self.next_invoice_number += 1
        self.save(update_fields=['next_invoice_number'])
        return num
"""
with open(os.path.join(BASE_DIR, "businesses", "models.py"), "w", encoding="utf-8") as f:
    f.write(businesses_models)

# businesses/forms.py
businesses_forms = """from django import forms
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
"""
with open(os.path.join(BASE_DIR, "businesses", "forms.py"), "w", encoding="utf-8") as f:
    f.write(businesses_forms)

# businesses/views.py
businesses_views = """from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Business, PLAN_LIMITS
from .forms import BusinessSettingsForm
from accounts.models import UserProfile

@login_required
def onboarding_view(request):
    if getattr(request, 'business', None):
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = BusinessSettingsForm(request.POST, request.FILES)
        if form.is_valid():
            business = form.save(commit=False)
            business.owner = request.user
            business.save()
            
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.business = business
            profile.save()
            
            messages.success(request, f"Shop '{business.name}' configured successfully!")
            return redirect('dashboard:index')
    else:
        form = BusinessSettingsForm(initial={
            'owner_name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
        })
        
    return render(request, 'businesses/settings.html', {'form': form, 'is_onboarding': True})

@login_required
def settings_view(request):
    business = getattr(request, 'business', None)
    if not business:
        return redirect('businesses:onboarding')
        
    if request.method == 'POST':
        form = BusinessSettingsForm(request.POST, request.FILES, instance=business)
        if form.is_valid():
            form.save()
            messages.success(request, "Business settings updated successfully!")
            return redirect('businesses:settings')
    else:
        form = BusinessSettingsForm(instance=business)
        
    return render(request, 'businesses/settings.html', {'form': form, 'business': business, 'is_onboarding': False})

@login_required
def plans_view(request):
    business = getattr(request, 'business', None)
    
    if request.method == 'POST':
        new_plan = request.POST.get('plan')
        if new_plan in PLAN_LIMITS and business:
            business.plan_tier = new_plan
            business.save(update_fields=['plan_tier'])
            messages.success(request, f"Your subscription plan has been updated to {PLAN_LIMITS[new_plan]['name']}!")
            return redirect('businesses:plans')
            
    return render(request, 'businesses/plans.html', {
        'business': business,
        'plans': PLAN_LIMITS,
        'current_plan': business.plan_tier if business else 'FREE'
    })
"""
with open(os.path.join(BASE_DIR, "businesses", "views.py"), "w", encoding="utf-8") as f:
    f.write(businesses_views)

# businesses/urls.py
businesses_urls = """from django.urls import path
from . import views

app_name = 'businesses'

urlpatterns = [
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('settings/', views.settings_view, name='settings'),
    path('plans/', views.plans_view, name='plans'),
]
"""
with open(os.path.join(BASE_DIR, "businesses", "urls.py"), "w", encoding="utf-8") as f:
    f.write(businesses_urls)

# businesses/admin.py
businesses_admin = """from django.contrib import admin
from .models import Business

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner_name', 'phone', 'city', 'plan_tier', 'created_at')
    list_filter = ('plan_tier', 'state', 'created_at')
    search_fields = ('name', 'owner_name', 'phone', 'email', 'gstin')
"""
with open(os.path.join(BASE_DIR, "businesses", "admin.py"), "w", encoding="utf-8") as f:
    f.write(businesses_admin)

print("Phase 2 (Accounts & Businesses) created successfully!")
