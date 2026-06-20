from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboards.services.canonical_analytics import build_canonical_analytics
from apps.dashboards.services.canonical_metrics import build_canonical_dashboard
from apps.dashboards.services.scope import resolve_canonical_scope


class DashboardsOverviewView(APIView):
    """Dashboard module entry."""

    def get(self, request):
        return Response(
            {
                "module": "dashboards",
                "status": "active",
                "endpoints": {
                    "metrics": "/api/v1/dashboards/metrics/",
                    "analytics": "/api/v1/dashboards/analytics/",
                },
            }
        )


class CanonicalDashboardMetricsView(APIView):
    """Operational dashboard backed by canonical task records."""

    def get(self, request):
        scope = resolve_canonical_scope(
            connection_id=(request.query_params.get("connection_id") or "").strip() or None,
            project_id=(request.query_params.get("project_id") or "").strip() or None,
            source_provider=(request.query_params.get("source_provider") or "").strip() or None,
        )

        payload = build_canonical_dashboard(
            project_id=scope.project_id,
            source_provider=scope.source_provider,
            connection_id=scope.connection_id,
        )
        return Response(payload)


class CanonicalAnalyticsView(APIView):
    """Analytics from canonical Trello task records."""

    def get(self, request):
        scope = resolve_canonical_scope(
            connection_id=(request.query_params.get("connection_id") or "").strip() or None,
            project_id=(request.query_params.get("project_id") or "").strip() or None,
            source_provider=(request.query_params.get("source_provider") or "trello").strip() or None,
        )

        payload = build_canonical_analytics(
            project_id=scope.project_id,
            source_provider=scope.source_provider,
            connection_id=scope.connection_id,
        )
        return Response(payload)
