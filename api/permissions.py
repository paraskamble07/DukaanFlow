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
