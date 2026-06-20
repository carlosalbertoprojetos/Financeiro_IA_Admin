from rest_framework.response import Response
from rest_framework.views import APIView


class AnalyticsOverviewView(APIView):
    """Analytics module entry — delegates to legacy analytics metrics API."""

    def get(self, request):
        return Response(
            {
                "module": "analytics",
                "status": "active",
                "endpoints": {
                    "metrics": "/api/v1/analytics/metrics/",
                    "overview": "/api/v1/analytics/metrics/overview/",
                    "team": "/api/v1/analytics/metrics/team/",
                    "cards": "/api/v1/analytics/metrics/cards/",
                    "gaps": "/api/v1/analytics/metrics/gaps/",
                },
                "legacy_prefix": "/api/analytics/",
            }
        )
