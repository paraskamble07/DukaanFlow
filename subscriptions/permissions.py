from rest_framework import permissions


def is_shopzen_admin(user):
    """Backend-enforced admin check: Django superuser flag OR the explicit
    SHOPZEN_ADMIN role. Never trust client-side claims."""
    if not (user and user.is_authenticated):
        return False
    if user.is_superuser:
        return True
    profile = getattr(user, 'userprofile', None)
    return profile is not None and profile.role == 'SHOPZEN_ADMIN'


class IsShopZenAdmin(permissions.BasePermission):
    message = 'ShopZen admin authorization required.'

    def has_permission(self, request, view):
        return is_shopzen_admin(request.user)
