from django.db import connection
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

APP_NAME = 'ShopZen'
APP_VERSION = '1.0.0'


class HealthAPIView(APIView):
    """Public liveness probe: used by the mobile app, Render health checks
    and uptime monitors. Never returns sensitive data."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        db_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except Exception:
            db_ok = False

        body = {
            'status': 'ok' if db_ok else 'degraded',
            'app': APP_NAME,
            'version': APP_VERSION,
            'database': 'up' if db_ok else 'down',
            'time': timezone.now().isoformat(),
        }
        # 200 when fully healthy, 503 lets monitors flag a broken database
        return Response(body, status=200 if db_ok else 503)
