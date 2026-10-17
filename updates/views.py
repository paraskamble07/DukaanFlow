from rest_framework import status
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from subscriptions.permissions import IsShopZenAdmin

from .models import AppRelease
from .serializers import AppReleaseSerializer, AppUpdateManifestSerializer


class AppUpdateCheckAPIView(APIView):
    """Public, unauthenticated update check (Phase 21).

    The client sends its platform and installed build number; the server
    answers with the newest active release for that platform plus the
    computed flags. The response is identical in shape whether or not an
    update exists so the endpoint cannot be abused as a probe.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        platform = (request.query_params.get('platform') or 'android').strip().lower()
        raw_code = (request.query_params.get('version_code') or request.query_params.get('build_number') or '0').strip()

        if platform not in {c for c, _ in AppRelease.PLATFORMS}:
            return Response(
                {'error': 'platform must be one of: android, ios.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            current_code = int(raw_code)
        except ValueError:
            return Response(
                {'error': 'version_code must be an integer build number.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if current_code < 0:
            return Response(
                {'error': 'version_code must be a non-negative build number.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        latest = (
            AppRelease.objects.filter(is_active=True, platform=platform)
            .order_by('-version_code')
            .first()
        )
        if latest is None:
            # Same key set as the release-found branch below (values null) so
            # clients always parse one stable shape.
            return Response({
                'platform': platform,
                'current_build_number': current_code,
                'update_available': False,
                'mandatory_update': False,
                'latest_version': None,
                'latest_build_number': None,
                'minimum_supported_version': None,
                'release_notes': None,
                'download_url': None,
                'checksum_sha256': None,
                'released_at': None,
            })

        update_available = latest.version_code > current_code
        # NOTE: `mandatory_update` is provided by the manifest serializer
        # below (it owns that logic); it is NOT set in this dict, because
        # `**manifest` would overwrite it after us.
        manifest = AppUpdateManifestSerializer(
            latest, context={'current_code': current_code}
        ).data

        return Response({
            'platform': platform,
            'current_build_number': current_code,
            'update_available': update_available,
            **manifest,
        })


class AppReleaseListCreateAPIView(APIView):
    """ShopZen admin: list published releases or publish a new one."""

    permission_classes = [IsAuthenticated, IsShopZenAdmin]

    def get(self, request):
        releases = AppRelease.objects.all().order_by('-version_code')
        return Response({
            'results': AppReleaseSerializer(releases, many=True).data,
        })

    def post(self, request):
        serializer = AppReleaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AppReleaseDetailAPIView(RetrieveUpdateDestroyAPIView):
    """ShopZen admin: fetch, edit or retire a single release."""

    permission_classes = [IsAuthenticated, IsShopZenAdmin]
    queryset = AppRelease.objects.all()
    serializer_class = AppReleaseSerializer
