from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboards.services.canonical_analytics import build_canonical_analytics
from apps.dashboards.services.canonical_report import (
    build_canonical_report_diagnosis,
    build_canonical_report_metrics,
)
from apps.dashboards.services.scope import resolve_canonical_scope
from reports.engine.pdf_builder import build_executive_report_pdf
from reports.exceptions import ReportValidationError


def _scope_from_request(request):
    connection_id = request.data.get("connection_id") or request.query_params.get("connection_id")
    board_id = request.data.get("board_id") or request.query_params.get("board_id")
    return resolve_canonical_scope(
        connection_id=str(connection_id).strip() if connection_id else None,
        project_id=str(board_id).strip() if board_id else None,
        source_provider="trello",
    )


class ReportsOverviewView(APIView):
    """Reports module entry — executive PDF from canonical Trello data."""

    def get(self, request):
        scope = resolve_canonical_scope(
            connection_id=(request.query_params.get("connection_id") or "").strip() or None,
            project_id=(request.query_params.get("board_id") or "").strip() or None,
            source_provider="trello",
        )
        analytics = build_canonical_analytics(
            project_id=scope.project_id,
            source_provider=scope.source_provider,
            connection_id=scope.connection_id,
        )
        return Response(
            {
                "module": "reports",
                "status": "active",
                "has_data": analytics["has_data"],
                "connection_id": scope.connection_id,
                "board_id": scope.project_id,
                "tasks_count": scope.task_count(),
                "reports": [
                    {
                        "id": "executive",
                        "label": "Relatório Executivo Operacional",
                        "method": "POST",
                        "path": "/api/v1/reports/executive/",
                        "type": "PDF",
                    },
                ],
                "last_generated_at": None,
            }
        )


class CanonicalExecutiveReportView(APIView):
    """Generate executive PDF from canonical Trello sync data."""

    def post(self, request):
        scope = _scope_from_request(request)
        metrics_bundle = build_canonical_report_metrics(
            project_id=scope.project_id,
            source_provider=scope.source_provider,
            connection_id=scope.connection_id,
        )

        total_tasks = metrics_bundle["dashboard"]["summary"]["total_tasks"]
        if total_tasks == 0:
            return Response(
                {
                    "error": (
                        "Nenhuma task do Trello sincronizada para esta conexão. "
                        "Execute um sync em Integrações antes de gerar o relatório."
                    ),
                    "connection_id": scope.connection_id,
                    "board_id": scope.project_id,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        diagnosis = build_canonical_report_diagnosis(metrics_bundle)
        board_name = scope.project_id or scope.connection_id or "Trello"

        try:
            pdf_bytes = build_executive_report_pdf(
                metrics_bundle,
                diagnosis,
                board_name=board_name,
            )
        except ReportValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        filename = f"executive-report-{board_name}.pdf"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
