from django.utils.deprecation import MiddlewareMixin
from businesses.models import Business

class TenantMiddleware(MiddlewareMixin):
    """Attaches current active business to request.business for logged-in users."""
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
