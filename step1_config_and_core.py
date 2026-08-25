import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def make_dirs():
    dirs = [
        "config",
        "core",
        "core/templatetags",
        "core/management",
        "core/management/commands",
        "accounts",
        "businesses",
        "customers",
        "products",
        "inventory",
        "sales",
        "purchases",
        "suppliers",
        "expenses",
        "payments",
        "invoices",
        "reports",
        "dashboard",
        "landing",
        "templates",
        "templates/accounts",
        "templates/businesses",
        "templates/customers",
        "templates/products",
        "templates/inventory",
        "templates/sales",
        "templates/purchases",
        "templates/suppliers",
        "templates/expenses",
        "templates/payments",
        "templates/invoices",
        "templates/reports",
        "templates/dashboard",
        "templates/landing",
        "static",
        "static/css",
        "static/js",
        "static/images",
        "media",
        "media/logos",
        "media/products",
        "tests",
    ]
    for d in dirs:
        os.makedirs(os.path.join(BASE_DIR, d), exist_ok=True)
        # Add __init__.py for python packages
        if not d.startswith("templates") and not d.startswith("static") and not d.startswith("media") and not d.startswith("tests") and d != "":
            init_file = os.path.join(BASE_DIR, d, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, "w", encoding="utf-8") as f:
                    f.write("")

make_dirs()

# 1. manage.py
manage_py = """#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
"""
with open(os.path.join(BASE_DIR, "manage.py"), "w", encoding="utf-8") as f:
    f.write(manage_py)

# 2. config/settings.py
settings_py = """import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dukaanflow-super-secret-key-change-in-prod')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,*').split(',') if h.strip()]

csrf_origins = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in csrf_origins.split(',') if o.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # DukaanFlow SaaS Apps
    'core',
    'accounts',
    'businesses',
    'customers',
    'products',
    'inventory',
    'suppliers',
    'purchases',
    'sales',
    'expenses',
    'payments',
    'invoices',
    'reports',
    'dashboard',
    'landing',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.TenantMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.business_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 6}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:index'
LOGOUT_REDIRECT_URL = 'landing:home'
"""
with open(os.path.join(BASE_DIR, "config", "settings.py"), "w", encoding="utf-8") as f:
    f.write(settings_py)

# 3. config/urls.py
urls_py = """from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('landing.urls', namespace='landing')),
    path('auth/', include('accounts.urls', namespace='accounts')),
    path('business/', include('businesses.urls', namespace='businesses')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('customers/', include('customers.urls', namespace='customers')),
    path('products/', include('products.urls', namespace='products')),
    path('inventory/', include('inventory.urls', namespace='inventory')),
    path('suppliers/', include('suppliers.urls', namespace='suppliers')),
    path('purchases/', include('purchases.urls', namespace='purchases')),
    path('sales/', include('sales.urls', namespace='sales')),
    path('expenses/', include('expenses.urls', namespace='expenses')),
    path('payments/', include('payments.urls', namespace='payments')),
    path('invoices/', include('invoices.urls', namespace='invoices')),
    path('reports/', include('reports.urls', namespace='reports')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
"""
with open(os.path.join(BASE_DIR, "config", "urls.py"), "w", encoding="utf-8") as f:
    f.write(urls_py)

# 4. config/wsgi.py & asgi.py
wsgi_py = """import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()
"""
with open(os.path.join(BASE_DIR, "config", "wsgi.py"), "w", encoding="utf-8") as f:
    f.write(wsgi_py)

asgi_py = """import os
from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_asgi_application()
"""
with open(os.path.join(BASE_DIR, "config", "asgi.py"), "w", encoding="utf-8") as f:
    f.write(asgi_py)

# 5. core/models.py
core_models_py = """from django.db import models

class TenantModel(models.Model):
    \"\"\"Abstract base model for multi-tenant isolation.\"\"\"
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_set",
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
"""
with open(os.path.join(BASE_DIR, "core", "models.py"), "w", encoding="utf-8") as f:
    f.write(core_models_py)

# 6. core/middleware.py
core_middleware_py = """from django.utils.deprecation import MiddlewareMixin
from businesses.models import Business

class TenantMiddleware(MiddlewareMixin):
    \"\"\"Attaches current active business to request.business for logged-in users.\"\"\"
    def process_request(self, request):
        request.business = None
        if request.user.is_authenticated:
            try:
                # Check user profile or owned business
                if hasattr(request.user, 'userprofile') and request.user.userprofile.business:
                    request.business = request.user.userprofile.business
                else:
                    request.business = Business.objects.filter(owner=request.user).first()
            except Exception:
                request.business = None
"""
with open(os.path.join(BASE_DIR, "core", "middleware.py"), "w", encoding="utf-8") as f:
    f.write(core_middleware_py)

# 7. core/context_processors.py
core_cp_py = """from datetime import date

def business_context(request):
    business = getattr(request, 'business', None)
    return {
        'current_business': business,
        'today': date.today(),
        'app_name': 'DukaanFlow',
        'app_tagline': 'Run your mobile shop smarter.',
    }
"""
with open(os.path.join(BASE_DIR, "core", "context_processors.py"), "w", encoding="utf-8") as f:
    f.write(core_cp_py)

# 8. core/templatetags/dukaan_tags.py
core_tags_py = """from django import template
from decimal import Decimal
import urllib.parse

register = template.Library()

@register.filter
def inr(value):
    \"\"\"Formats a decimal or float into Indian Rupee format: ₹1,25,000.00\"\"\"
    if value is None or value == '':
        return "₹0.00"
    try:
        val = Decimal(str(value))
    except Exception:
        return f"₹{value}"
    
    is_neg = val < 0
    val = abs(val)
    
    # Split integer and decimal parts
    parts = f"{val:.2f}".split('.')
    int_part = parts[0]
    dec_part = parts[1]
    
    if len(int_part) <= 3:
        formatted_int = int_part
    else:
        last3 = int_part[-3:]
        remaining = int_part[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted_int = ",".join(groups) + "," + last3
        
    prefix = "-₹" if is_neg else "₹"
    return f"{prefix}{formatted_int}.{dec_part}"

@register.filter
def urlencode_text(value):
    if not value:
        return ""
    return urllib.parse.quote(str(value))

@register.filter
def multiply(value, arg):
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except Exception:
        return 0

@register.filter
def subtract(value, arg):
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except Exception:
        return 0
"""
with open(os.path.join(BASE_DIR, "core", "templatetags", "dukaan_tags.py"), "w", encoding="utf-8") as f:
    f.write(core_tags_py)

with open(os.path.join(BASE_DIR, "core", "templatetags", "__init__.py"), "w", encoding="utf-8") as f:
    f.write("")

# 9. core/utils.py
core_utils_py = """from decimal import Decimal
import urllib.parse
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def format_inr(val):
    if val is None:
        return "₹0.00"
    try:
        d = Decimal(str(val))
    except Exception:
        return f"₹{val}"
    is_neg = d < 0
    d = abs(d)
    parts = f"{d:.2f}".split('.')
    int_part = parts[0]
    dec_part = parts[1]
    if len(int_part) <= 3:
        formatted_int = int_part
    else:
        last3 = int_part[-3:]
        rem = int_part[:-3]
        groups = []
        while len(rem) > 2:
            groups.insert(0, rem[-2:])
            rem = rem[:-2]
        if rem:
            groups.insert(0, rem)
        formatted_int = ",".join(groups) + "," + last3
    return f"{'-' if is_neg else ''}₹{formatted_int}.{dec_part}"

def build_whatsapp_url(phone, message):
    if not phone:
        return ""
    # Clean phone to 10-12 digits, prepend 91 if 10 digits
    clean_phone = "".join(ch for ch in str(phone) if ch.isdigit())
    if len(clean_phone) == 10:
        clean_phone = "91" + clean_phone
    encoded_msg = urllib.parse.quote(message)
    return f"https://wa.me/{clean_phone}?text={encoded_msg}"

def business_required(view_func):
    \"\"\"Decorator that ensures user is logged in and has an active business.\"\"\"
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not getattr(request, 'business', None):
            messages.warning(request, "Please set up your business details first to continue.")
            return redirect('businesses:onboarding')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
"""
with open(os.path.join(BASE_DIR, "core", "utils.py"), "w", encoding="utf-8") as f:
    f.write(core_utils_py)

print("Phase 1 (Config & Core) created successfully!")
