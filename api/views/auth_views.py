from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from accounts.models import UserProfile
from businesses.models import Business, PLAN_LIMITS
from api.serializers import UserSerializer, BusinessSerializer
from api.permissions import HasActiveBusiness

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')
        full_name = request.data.get('full_name', '').strip()
        shop_name = request.data.get('shop_name', '').strip()
        phone = request.data.get('phone', '').strip()

        if not all([email, password, full_name, shop_name, phone]):
            return Response({'error': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
            return Response({'error': 'This email is already registered. Please login instead.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name
        )

        business = Business.objects.create(
            owner=user,
            name=shop_name,
            owner_name=full_name,
            phone=phone,
            email=email,
            plan_tier='FREE'
        )

        UserProfile.objects.create(
            user=user,
            business=business,
            phone=phone,
            role='OWNER'
        )

        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Shop registered successfully!',
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'user': UserSerializer(user).data,
            'business': BusinessSerializer(business, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)

class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email_or_username = request.data.get('email', '').strip()
        password = request.data.get('password', '')

        if not email_or_username or not password:
            return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=email_or_username, password=password)
        if not user and '@' in email_or_username:
            user_obj = User.objects.filter(email__iexact=email_or_username).first()
            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)

        if not user:
            return Response({'error': 'Incorrect email or password.'}, status=status.HTTP_401_UNAUTHORIZED)

        # Get business
        business = None
        if hasattr(user, 'userprofile') and user.userprofile.business:
            business = user.userprofile.business
        else:
            business = Business.objects.filter(owner=user).first()

        refresh = RefreshToken.for_user(user)
        return Response({
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'user': UserSerializer(user).data,
            'business': BusinessSerializer(business, context={'request': request}).data if business else None,
        })

class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # TenantMiddleware runs before DRF's JWT authentication populates
        # request.user, so for Bearer-token clients request.business is None
        # here — resolve the business from the authenticated user directly
        # (same fallback LoginAPIView uses).
        business = getattr(request, 'business', None)
        if business is None:
            if hasattr(user, 'userprofile') and user.userprofile.business:
                business = user.userprofile.business
            else:
                business = Business.objects.filter(owner=user).first()
        return Response({
            'user': UserSerializer(user).data,
            'business': BusinessSerializer(business, context={'request': request}).data if business else None,
        })

    def put(self, request):
        user = request.user
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.phone = request.data.get('phone', profile.phone)
        profile.save()

        return Response({
            'message': 'Profile updated successfully.',
            'user': UserSerializer(user).data
        })

class BusinessSettingsAPIView(APIView):
    permission_classes = [IsAuthenticated, HasActiveBusiness]

    def get(self, request):
        return Response(BusinessSerializer(request.business, context={'request': request}).data)

    def put(self, request):
        business = request.business
        serializer = BusinessSerializer(business, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Business settings updated successfully.',
                'business': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SubscriptionPlansAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = getattr(request, 'business', None)
        return Response({
            'current_plan': business.plan_tier if business else 'FREE',
            'plans': PLAN_LIMITS
        })

    def post(self, request):
        business = getattr(request, 'business', None)
        if not business:
            return Response({'error': 'No active business attached.'}, status=status.HTTP_400_BAD_REQUEST)

        plan = request.data.get('plan')
        if plan in PLAN_LIMITS:
            business.plan_tier = plan
            business.save(update_fields=['plan_tier'])
            return Response({
                'message': f'Subscription upgraded to {PLAN_LIMITS[plan]["name"]}!',
                'business': BusinessSerializer(business, context={'request': request}).data
            })
        return Response({'error': 'Invalid subscription plan.'}, status=status.HTTP_400_BAD_REQUEST)
