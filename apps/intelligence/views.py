from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.intelligence.providers.base import list_providers
from apps.intelligence.services.dashboard.executive import build_executive_dashboard
from apps.intelligence.services.bottleneck_detector.detector import detect_bottlenecks
from apps.intelligence.services.enrichment.engine import enrich_board
from apps.intelligence.services.executive_summary.agent import build_executive_summary
from apps.intelligence.services.kpi.engine import compute_board_kpis
from apps.intelligence.services.knowledge.extractor import get_knowledge_base
from apps.intelligence.services.operational_score.scorer import compute_operational_score, get_score_history
from apps.intelligence.services.orchestrator import run_intelligence_pipeline
from apps.intelligence.services.predictive.engine import predict_board
from apps.intelligence.services.report_builder import build_executive_report
from apps.intelligence.services.risk_engine.scorer import assess_board_risk
from apps.intelligence.services.timeline.engine import build_card_timeline, build_timeline_events_for_board
from integrations.trello.models import Board, Card


class IntelligenceOverviewView(APIView):
    def get(self, request: Request) -> Response:
        return Response(
            {
                "module": "intelligence",
                "version": "EOR_V2",
                "providers": list_providers(),
                "endpoints": [
                    "pipeline/",
                    "timeline/",
                    "kpis/",
                    "bottlenecks/",
                    "risks/",
                    "predictions/",
                    "score/",
                    "executive-summary/",
                    "report/",
                    "knowledge/",
                ],
            }
        )


class IntelligencePipelineView(APIView):
    def post(self, request: Request) -> Response:
        board_id = request.data.get("board_id") or request.query_params.get("board_id")
        if not board_id:
            return Response({"error": "board_id required"}, status=status.HTTP_400_BAD_REQUEST)
        use_ai = request.data.get("use_ai", True)
        result = run_intelligence_pipeline(board_id, use_ai=use_ai)
        return Response(result)


class TimelineView(APIView):
    def get(self, request: Request) -> Response:
        board_id = request.query_params.get("board_id")
        card_id = request.query_params.get("card_id")
        if card_id:
            card = Card.objects.filter(trello_id=card_id).first()
            if not card:
                return Response({"error": "Card not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response({"card_id": card_id, "timeline": build_card_timeline(card)})
        if not board_id:
            return Response({"error": "board_id or card_id required"}, status=status.HTTP_400_BAD_REQUEST)
        count = build_timeline_events_for_board(board_id)
        return Response({"board_id": board_id, "events_built": count})


class KPIView(APIView):
    def get(self, request: Request) -> Response:
        board_id = request.query_params.get("board_id")
        if not board_id:
            return Response({"error": "board_id required"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(compute_board_kpis(board_trello_id=board_id))


class BottleneckView(APIView):
    def get(self, request: Request) -> Response:
        board_id = request.query_params.get("board_id")
        if not board_id:
            return Response({"error": "board_id required"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(detect_bottlenecks(board_trello_id=board_id))


class RiskView(APIView):
    def get(self, request: Request) -> Response:
        board_id = request.query_params.get("board_id")
        if not board_id:
            return Response({"error": "board_id required"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(assess_board_risk(board_trello_id=board_id))


class PredictiveView(APIView):
    def get(self, request: Request) -> Response:
        board_id = request.query_params.get("board_id")
        if not board_id:
            return Response({"error": "board_id required"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(predict_board(board_trello_id=board_id))


class OperationalScoreView(APIView):
    def get(self, request: Request) -> Response:
        board_id = request.query_params.get("board_id")
        if not board_id:
            return Response({"error": "board_id required"}, status=status.HTTP_400_BAD_REQUEST)
        result = compute_operational_score(board_trello_id=board_id)
        history = get_score_history(board_id)
        return Response(
            {
                "score": result.score,
                "level": result.level,
                "components": result.components,
                "history": history,
            }
        )


class ExecutiveSummaryView(APIView):
    def get(self, request: Request) -> Response:
        board_id = request.query_params.get("board_id")
        if not board_id:
            return Response({"error": "board_id required"}, status=status.HTTP_400_BAD_REQUEST)
        use_ai = request.query_params.get("use_ai", "false").lower() == "true"
        return Response(build_executive_summary(board_trello_id=board_id, use_ai=use_ai))


class ExecutiveReportView(APIView):
    def get(self, request: Request) -> Response:
        board_id = request.query_params.get("board_id")
        if not board_id:
            return Response({"error": "board_id required"}, status=status.HTTP_400_BAD_REQUEST)
        use_ai = request.query_params.get("use_ai", "false").lower() == "true"
        return Response(build_executive_report(board_trello_id=board_id, use_ai=use_ai))


class KnowledgeBaseView(APIView):
    def get(self, request: Request) -> Response:
        board_id = request.query_params.get("board_id")
        if not board_id:
            return Response({"error": "board_id required"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"entries": get_knowledge_base(board_id)})


class ExecutiveDashboardView(APIView):
    def get(self, request: Request) -> Response:
        board_id = request.query_params.get("board_id")
        level = request.query_params.get("level", "operational")
        if not board_id:
            return Response({"error": "board_id required"}, status=status.HTTP_400_BAD_REQUEST)
        valid_levels = ("operational", "management", "director", "ceo")
        if level not in valid_levels:
            return Response(
                {"error": f"level must be one of {valid_levels}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(build_executive_dashboard(board_id, level=level))


class EnrichmentView(APIView):
    def post(self, request: Request) -> Response:
        board_id = request.data.get("board_id") or request.query_params.get("board_id")
        if not board_id:
            return Response({"error": "board_id required"}, status=status.HTTP_400_BAD_REQUEST)
        contexts = enrich_board(board_id)
        return Response(
            {
                "board_id": board_id,
                "count": len(contexts),
                "enrichments": [
                    {
                        "card_id": c.card_id,
                        "priority": c.priority,
                        "urgency": c.urgency,
                        "area": c.area,
                        "objective": c.objective,
                    }
                    for c in contexts
                ],
            }
        )
