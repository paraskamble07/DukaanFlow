from rest_framework import permissions
from businesses.models import Business


class HasActiveBusiness(permissions.BasePermission):
    """Ensures that the requesting authenticated user is linked to an active Business."""
    message = "You must have an active shop/business configured to perform this action."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # Attach business to request if not already done by middleware
        if not getattr(request, 'business', None):
            if hasattr(request.user, 'userprofile') and request.user.userprofile.business:
                request.business = request.user.userprofile.business
            else:
                request.business = Business.objects.filter(owner=request.user).first()

        return request.business is not None


# Per-module permission gates. The OWNER may do everything; STAFF may only do
# the modules explicitly granted on their UserProfile. SHOPZEN_ADMIN is the
# platform admin (unrelated to any one shop) and is handled separately.
MODULE_PERMISSIONS = {
    'products': 'products',
    'inventory': 'inventory',
    'suppliers': 'suppliers',
    'purchases': 'purchases',
    'sales': 'sales',
    'customers': 'customers',
    'payments': 'payments',
    'expenses': 'expenses',
    'reports': 'reports',
    'settings': 'settings',
    'whatsapp': 'whatsapp',
    'sms': 'sms',
}


def is_owner(user):
    return getattr(user, 'userprofile', None) and user.userprofile.role == 'OWNER'


def is_staff(user):
    return getattr(user, 'userprofile', None) and user.userprofile.role == 'STAFF'


def can(user, module):
    """True if the user is allowed to use `module`.

    Rules:
      - unauthenticated -> False (handled by IsAuthenticated elsewhere)
      - OWNER          -> everything
      - SHOPZEN_ADMIN  -> everything (platform admin)
      - STAFF          -> only modules granted on their profile
    """
    if not user or not user.is_authenticated:
        return False
    profile = getattr(user, 'userprofile', None)
    if profile is None:
        return False
    if profile.role in ('OWNER', 'SHOPZEN_ADMIN'):
        return True
    if profile.role == 'STAFF':
        return module in (profile.permissions or [])
    return False


class ModulePermission(permissions.BasePermission):
    """Gate a view behind a single module permission (see MODULE_PERMISSIONS).

    DRF instantiates every entry in ``permission_classes`` with no
    arguments, so the classes listed in ``permission_classes`` must be
    subclasses whose ``__init__`` takes no required args. Use the named
    subclasses below (``ProductsPermission``, ``ReportsPermission`` …)
    in view declarations. The ``ModulePermission('products')`` form is
    still valid for ad-hoc checks but cannot be listed as a class.
    """

    module = None

    def __init__(self, module=None):
        if module is not None:
            self.module = module

    def has_permission(self, request, view):
        return can(request.user, self.module)


# One named subclass per module so views can reference them as classes.
class ProductsPermission(ModulePermission):
    def __init__(self):
        super().__init__('products')


class InventoryPermission(ModulePermission):
    def __init__(self):
        super().__init__('inventory')


class SuppliersPermission(ModulePermission):
    def __init__(self):
        super().__init__('suppliers')


class PurchasesPermission(ModulePermission):
    def __init__(self):
        super().__init__('purchases')


class SalesPermission(ModulePermission):
    def __init__(self):
        super().__init__('sales')


class CustomersPermission(ModulePermission):
    def __init__(self):
        super().__init__('customers')


class PaymentsPermission(ModulePermission):
    def __init__(self):
        super().__init__('payments')


class ExpensesPermission(ModulePermission):
    def __init__(self):
        super().__init__('expenses')


class ReportsPermission(ModulePermission):
    def __init__(self):
        super().__init__('reports')


class SettingsPermission(ModulePermission):
    def __init__(self):
        super().__init__('settings')


class WhatsappPermission(ModulePermission):
    def __init__(self):
        super().__init__('whatsapp')


class SmsPermission(ModulePermission):
    def __init__(self):
        super().__init__('sms')


class OwnerOnly(permissions.BasePermission):
    """Only the OWNER of the business may access this view."""
    message = "Only the shop owner may perform this action."

    def has_permission(self, request, view):
        return is_owner(request.user)


class OwnerOrStaffWith(permissions.BasePermission):
    """Staff may access only if the module is granted; owners always pass."""
    def __init__(self, module):
        self.module = module

    def has_permission(self, request, view):
        return can(request.user, self.module)


class IsShopOwnerOrStaff(permissions.BasePermission):
    """Owner or staff with the module granted; SHOPZEN_ADMIN bypasses."""
    def __init__(self, module):
        self.module = module

    def has_permission(self, request, view):
        return can(request.user, self.module)


# Field-level privacy: these are the ONLY sensitive fields. Employees must never
# see purchase price, supplier cost, profit, or owner-only financial reports.
SENSITIVE_PRODUCT_FIELDS = {'purchase_price', 'profit_margin'}
SENSITIVE_SALE_FIELDS = {'gross_profit'}
SENSITIVE_REPORT_FIELDS = {'gross_profit', 'profit', 'supplier_cost', 'total_cost'}


def is_shopzen_admin(user):
    return getattr(user, 'userprofile', None) and user.userprofile.role == 'SHOPZEN_ADMIN'


def is_field_sensitive(field, user):
    """Return True if `field` must be hidden from this user (employees)."""
    if is_owner(user) or is_shopzen_admin(user):
        return False
    return (field in SENSITIVE_PRODUCT_FIELDS
            or field in SENSITIVE_SALE_FIELDS
            or field in SENSITIVE_REPORT_FIELDS)