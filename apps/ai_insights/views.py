from rest_framework.response import Response
from rest_framework.views import APIView


class AiInsightsOverviewView(APIView):
    """AI insights module entry — delegates to legacy ai analyst API."""

    def get(self, request):
        return Response(
            {
                "module": "ai_insights",
                "status": "active",
                "endpoints": {
                    "analyze": "/api/v1/ai-insights/analyze/",
                },
                "legacy_prefix": "/api/ai/",
            }
        )
