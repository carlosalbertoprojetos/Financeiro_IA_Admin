from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.intelligence.services.report_query.domain.dsl_parser import parse_report_dsl
from apps.intelligence.services.report_query.domain.filters import ReportQueryPayload, ReportTemplate
from apps.intelligence.services.report_query.engine.executor import execute_report_query


class ReportQueryView(APIView):
    """
    POST /api/reports/query — segmented report generation from combined filters.

    Accepts JSON payload or DSL text via ``query_dsl`` / ``report_dsl`` field.
    """

    def post(self, request: Request) -> Response:
        data = self._resolve_payload(request)
        if not data.get("board_id"):
            return Response({"error": "board_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = getattr(request, "user", None)
        generated_by = str(getattr(user, "username", None) or data.get("generated_by") or "anonymous")

        try:
            payload = ReportQueryPayload.from_dict({**data, "generated_by": generated_by})
        except (ValueError, KeyError) as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        result = execute_report_query(payload)
        return Response(result)

    def get(self, request: Request) -> Response:
        return Response(
            {
                "endpoint": "POST /api/reports/query/",
                "description": "Segmented report generation with combined filters",
                "supports_dsl": True,
                "report_types": [
                    {"value": t.value, "label": t.value.title()}
                    for t in ReportTemplate
                ],
                "example_json": {
                    "board_id": "YOUR_BOARD_ID",
                    "report_type": "EXECUTIVO",
                    "period": "last_30_days",
                    "title_prefix": "AQUI",
                    "labels": ["Financeiro", "Jurídico"],
                    "label_operator": "and",
                    "members": ["Carlos"],
                    "status": ["atrasado", "bloqueado"],
                    "status_operator": "or",
                    "metrics": ["LEAD_TIME", "CYCLE_TIME", "RISK_SCORE", "SLA"],
                    "group_by": ["LABELS", "MEMBERS"],
                    "sort_by": "RISK_SCORE",
                    "sort_order": "DESC",
                    "limit": 100,
                },
                "example_dsl": (
                    "TYPE = EXECUTIVE\n"
                    "PERIOD = LAST_30_DAYS\n"
                    "LABELS = Financeiro AND Jurídico\n"
                    "MEMBERS = Carlos\n"
                    "TITLE_PREFIX = [AQUI]\n"
                    "STATUS = (ATRASADO OR BLOQUEADO)\n"
                    "METRICS = LEAD_TIME, CYCLE_TIME, RISK_SCORE, SLA\n"
                    "GROUP_BY = LABELS, MEMBERS\n"
                    "SORT = RISK_SCORE DESC\n"
                    "LIMIT = 100"
                ),
            }
        )

    def _resolve_payload(self, request: Request) -> dict:
        data = dict(request.data) if isinstance(request.data, dict) else {}
        dsl = data.pop("query_dsl", None) or data.pop("report_dsl", None)
        if dsl:
            parsed = parse_report_dsl(str(dsl))
            return {**parsed, **data}
        return data
