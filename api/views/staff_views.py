"""Staff management (owner-only).

The RBAC layer (api.permissions) already gates every module for STAFF users,
but until now there was no way to *create* a staff member, so the whole
staff-login feature was unreachable. These endpoints let the shop owner
manage their staff and per-module grants; everything is enforced server-side
and the app only reflects it.
"""
from django.contrib.auth.models import User
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserProfile
from api.permissions import HasActiveBusiness, OwnerOnly, MODULE_PERMISSIONS

# Modules a staff member may be granted. Kept in sync with the RBAC map in
# api.permissions (the enforcement side), never derived from client input.
ALLOWED_MODULES = sorted(MODULE_PERMISSIONS.keys())


class StaffMemberSerializer(serializers.ModelSerializer):
    """A staff account of the requesting owner's business."""
    email = serializers.EmailField(source='user.email')
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    created_at = serializers.DateTimeField(source='user.date_joined', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'email', 'first_name', 'phone', 'permissions', 'is_active', 'created_at']

    def validate_permissions(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('permissions must be a list of module names.')
        unknown = {str(m) for m in value} - set(ALLOWED_MODULES)
        if unknown:
            raise serializers.ValidationError(
                f'Unknown module(s): {", ".join(sorted(unknown))}. '
                f'Allowed: {", ".join(ALLOWED_MODULES)}.')
        return sorted({str(m) for m in value})


class StaffListCreateAPIView(APIView):
    """List the shop's staff, or invite a new staff member."""
    permission_classes = [IsAuthenticated, HasActiveBusiness, OwnerOnly]

    def get(self, request):
        staff = (
            UserProfile.objects
            .filter(business=request.business, role='STAFF')
            .select_related('user')
            .order_by('-user__date_joined')
        )
        return Response({
            'results': StaffMemberSerializer(staff, many=True).data,
            'allowed_modules': ALLOWED_MODULES,
        })

    def post(self, request):
        business = request.business
        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password') or ''
        first_name = (request.data.get('first_name') or '').strip()

        if not email or not password:
            return Response({
                'error': 'Email and a password are required to add a staff member.'
            }, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email__iexact=email).exists():
            return Response({
                'error': 'A user with this email already exists.',
                'code': 'DUPLICATE_EMAIL',
            }, status=status.HTTP_409_CONFLICT)
        if len(password) < 8:
            return Response({
                'error': 'Staff password must be at least 8 characters.',
            }, status=status.HTTP_400_BAD_REQUEST)

        perms_serializer = StaffMemberSerializer(data=request.data)
        if not perms_serializer.is_valid():
            return Response(perms_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=email, email=email, password=password, first_name=first_name)
        profile = UserProfile.objects.create(
            user=user, business=business, role='STAFF',
            phone=(request.data.get('phone') or '').strip(),
            permissions=perms_serializer.validated_data['permissions'])
        return Response(StaffMemberSerializer(profile).data, status=status.HTTP_201_CREATED)


class StaffDetailAPIView(APIView):
    """Update a staff member's grants / phone, or deactivate them."""
    permission_classes = [IsAuthenticated, HasActiveBusiness, OwnerOnly]

    def _get_staff(self, request, pk):
        return (
            UserProfile.objects
            .filter(pk=pk, business=request.business, role='STAFF')
            .select_related('user').first()
        )

    def patch(self, request, pk):
        profile = self._get_staff(request, pk)
        if profile is None:
            return Response({'error': 'Staff member not found.'},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = StaffMemberSerializer(profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if 'permissions' in serializer.validated_data:
            profile.permissions = serializer.validated_data['permissions']
        if 'phone' in serializer.validated_data:
            profile.phone = serializer.validated_data['phone']
        if 'first_name' in serializer.validated_data:
            profile.user.first_name = serializer.validated_data['first_name']
            profile.user.save(update_fields=['first_name'])
        if 'reactivate' in request.data and request.data['reactivate'] is True:
            profile.user.is_active = True
            profile.user.save(update_fields=['is_active'])
        profile.save()
        return Response(StaffMemberSerializer(profile).data)

    def delete(self, request, pk):
        """Deactivate the staff login.

        Never deletes the account: their bills, payments and stock movements
        stay attributable to them, and the login simply stops working.
        """
        profile = self._get_staff(request, pk)
        if profile is None:
            return Response({'error': 'Staff member not found.'},
                            status=status.HTTP_404_NOT_FOUND)
        profile.user.is_active = False
        profile.user.save(update_fields=['is_active'])
        return Response({
            'message': f"{profile.user.email} can no longer log in. Their history is kept.",
        }, status=status.HTTP_200_OK)
