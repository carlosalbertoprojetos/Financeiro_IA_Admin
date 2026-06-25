from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.intelligence.services.business_value.attribution.engine import aggregate_by_dimension
from apps.intelligence.services.business_value.pipeline import build_executive_value_dashboard
from apps.intelligence.services.business_value.trends.engine import compute_value_trends


class ValueOverviewView(APIView):
    def get(self, request: Request) -> Response:
        return Response({
            "endpoints": {
                "dashboard": "GET /api/value/dashboard/",
                "projects": "GET /api/value/projects/",
                "teams": "GET /api/value/teams/",
                "actions": "GET /api/value/actions/",
                "trends": "GET /api/value/trends/",
            },
            "config_env": {
                "hourly_rate": "BVE_HOURLY_RATE_BRL",
                "base_impact": "BVE_BASE_IMPACT_BRL",
            },
        })


class ValueDashboardView(APIView):
    def get(self, request: Request) -> Response:
        board_id = str(request.query_params.get("board_id", ""))
        days = int(request.query_params.get("days", 90))
        return Response(build_executive_value_dashboard(board_id=board_id, days=days))


class ValueProjectsView(APIView):
    def get(self, request: Request) -> Response:
        board_id = str(request.query_params.get("board_id", ""))
        days = int(request.query_params.get("days", 90))
        return Response({"projects": aggregate_by_dimension("project", board_id=board_id, days=days)})


class ValueTeamsView(APIView):
    def get(self, request: Request) -> Response:
        board_id = str(request.query_params.get("board_id", ""))
        days = int(request.query_params.get("days", 90))
        return Response({"teams": aggregate_by_dimension("team", board_id=board_id, days=days)})


class ValueActionsView(APIView):
    def get(self, request: Request) -> Response:
        board_id = str(request.query_params.get("board_id", ""))
        days = int(request.query_params.get("days", 90))
        return Response({"actions": aggregate_by_dimension("action", board_id=board_id, days=days)})


class ValueTrendsView(APIView):
    def get(self, request: Request) -> Response:
        board_id = str(request.query_params.get("board_id", ""))
        days = int(request.query_params.get("days", 365))
        return Response(compute_value_trends(board_id=board_id, days=days))
