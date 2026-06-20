from rest_framework.response import Response
from rest_framework.views import APIView


class PlatformOverviewView(APIView):
    """TIP platform API root."""

    def get(self, request):
        return Response(
            {
                "platform": "TIP",
                "name": "Trello Intelligence Platform",
                "version": "1.0.0",
                "modules": {
                    "data_sources": "/api/v1/data-sources/",
                    "dashboards": "/api/v1/dashboards/",
                    "analytics": "/api/v1/analytics/",
                    "reports": "/api/v1/reports/",
                    "ai_insights": "/api/v1/ai-insights/",
                    "exports": "/api/v1/exports/",
                    "users": "/api/v1/users/",
                    "settings": "/api/v1/settings/",
                },
                "legacy_api": {
                    "dashboard": "/api/dashboard/",
                    "analytics": "/api/analytics/",
                    "reports": "/api/reports/",
                    "ai": "/api/ai/",
                    "trello": "/api/integrations/trello/",
                },
            }
        )
