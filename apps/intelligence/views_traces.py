from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.intelligence.services.observability.dashboard import build_dashboard_stats, build_insights_summary
from apps.intelligence.services.observability.storage import load_trace, load_traces_by_query_id


class TraceDetailView(APIView):
    """GET /api/traces/{trace_id}/"""

    def get(self, request: Request, trace_id: str) -> Response:
        trace = load_trace(trace_id)
        if not trace:
            return Response({"error": "Trace not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(trace)


class TraceByQueryView(APIView):
    """GET /api/traces/query/{query_id}/"""

    def get(self, request: Request, query_id: str) -> Response:
        traces = load_traces_by_query_id(query_id)
        return Response({"query_id": query_id, "traces": traces, "count": len(traces)})


class TraceInsightsView(APIView):
    """GET /api/traces/insights/"""

    def get(self, request: Request) -> Response:
        limit = int(request.query_params.get("limit", 20))
        return Response({"insights": build_insights_summary(limit=limit)})


class TraceDashboardView(APIView):
    """GET /api/traces/dashboard/ — system visibility dashboard."""

    def get(self, request: Request) -> Response:
        board_id = str(request.query_params.get("board_id", ""))
        return Response(build_dashboard_stats(board_id=board_id))


class TracesOverviewView(APIView):
    def get(self, request: Request) -> Response:
        return Response({
            "endpoints": {
                "trace_detail": "GET /api/traces/{trace_id}/",
                "trace_by_query": "GET /api/traces/query/{query_id}/",
                "insights": "GET /api/traces/insights/",
                "dashboard": "GET /api/traces/dashboard/",
            },
            "debug_mode_env": "EOR_DEBUG_MODE=true",
        })
