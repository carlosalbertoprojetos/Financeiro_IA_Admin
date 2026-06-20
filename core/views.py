from django.db import connection
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Simple healthcheck endpoint for load balancers and monitoring."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        db_status = "ok"
        try:
            connection.ensure_connection()
        except Exception:
            db_status = "error"

        status_code = 200 if db_status == "ok" else 503

        return Response(
            {
                "status": "ok" if db_status == "ok" else "degraded",
                "service": "tip_backend",
                "database": db_status,
                "timestamp": timezone.now().isoformat(),
            },
            status=status_code,
        )
