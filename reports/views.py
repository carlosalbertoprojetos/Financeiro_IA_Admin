from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ai.analyst import analyze_metrics
from ai.exceptions import AIAnalysisError, AIConfigurationError
from analytics.adapters import load_board_records
from analytics.services.builders import build_gaps, build_overview, build_team
from integrations.trello.models import Board
from reports.engine.pdf_builder import build_executive_report_pdf
from reports.exceptions import ReportValidationError


class ExecutiveReportView(APIView):
    """Generate executive PDF from metrics + AI diagnosis."""

    def post(self, request):
        metrics = request.data.get("metrics")
        diagnosis = request.data.get("diagnosis")

        if metrics and diagnosis:
            return self._pdf_response(metrics, diagnosis, board_id=metrics.get("board_id", "board"))

        board_id = request.data.get("board_id") or request.query_params.get("board_id")
        if not board_id:
            return Response(
                {"error": "Provide board_id or both metrics and diagnosis"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        include_removed = str(
            request.data.get("include_removed", request.query_params.get("include_removed", "false"))
        ).lower() == "true"
        include_team = str(
            request.data.get("include_team", request.query_params.get("include_team", "true"))
        ).lower() == "true"
        period = request.data.get("period") or request.query_params.get("period", "day")

        cards, actions = load_board_records(
            board_trello_id=board_id,
            include_removed=include_removed,
            reference_time=timezone.now(),
        )
        now = timezone.now()

        overview = build_overview(
            cards,
            actions,
            board_id=board_id,
            reference_time=now,
            throughput_period=period,
        )
        gaps = build_gaps(cards, actions, board_id=board_id, reference_time=now)

        aggregated_metrics = {
            "board_id": board_id,
            "generated_at": now.isoformat(),
            "overview": overview,
            "gaps": gaps,
        }
        if include_team:
            aggregated_metrics["team"] = build_team(
                cards,
                actions,
                board_id=board_id,
                reference_time=now,
            )

        try:
            diagnosis = analyze_metrics(aggregated_metrics)
        except AIConfigurationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except AIAnalysisError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        board = Board.objects.filter(trello_id=board_id).first()
        board_name = board.name if board else board_id
        return self._pdf_response(aggregated_metrics, diagnosis, board_id=board_id, board_name=board_name)

    def _pdf_response(
        self,
        metrics: dict,
        diagnosis: dict,
        *,
        board_id: str,
        board_name: str | None = None,
    ) -> HttpResponse | Response:
        try:
            pdf_bytes = build_executive_report_pdf(
                metrics,
                diagnosis,
                board_name=board_name or board_id,
            )
        except ReportValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        filename = f"executive-report-{board_id}.pdf"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
