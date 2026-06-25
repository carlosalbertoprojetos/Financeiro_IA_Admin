from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.intelligence.services.eql.errors import EQLError
from apps.intelligence.services.query_engine.runner import execute_eql_query


class EQLReportView(APIView):
    """
    POST /api/reports/eql — execute EOR Query Language reports.

    Payload: { "board_id": "...", "query": "REPORT:\\nTYPE = EXECUTIVE\\n..." }
    """

    def post(self, request: Request) -> Response:
        data = dict(request.data) if isinstance(request.data, dict) else {}
        query_text = data.get("query") or data.get("eql") or data.get("query_dsl")
        board_id = str(data.get("board_id", "")).strip()

        if not query_text:
            return Response(
                {"error": {"code": "SYNTAX_ERROR", "message": "query field is required"}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not board_id and "BOARD_ID" not in str(query_text).upper():
            return Response(
                {"error": {"code": "MISSING_BOARD_ID", "message": "board_id is required"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = getattr(request, "user", None)
        user_id = str(getattr(user, "username", None) or data.get("user_id") or "anonymous")
        use_cache = data.get("use_cache", True)

        try:
            result = execute_eql_query(
                str(query_text),
                board_id=board_id,
                user_id=user_id,
                use_cache=bool(use_cache),
            )
            return Response(result)
        except EQLError as exc:
            return Response({"error": exc.to_dict()}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"error": {"code": "EXECUTION_ERROR", "message": str(exc)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request: Request) -> Response:
        return Response(
            {
                "endpoint": "POST /api/reports/eql/",
                "description": "EOR Query Language (EQL) report execution",
                "spec": "/docs/EQL_SPEC.md",
                "example": {
                    "board_id": "YOUR_BOARD_ID",
                    "query": (
                        "REPORT:\n"
                        "TYPE = EXECUTIVE\n\n"
                        "FILTER:\n"
                        "PERIOD = LAST_30_DAYS\n"
                        "LABELS = Financeiro\n"
                        "MEMBERS = Carlos\n"
                        "STATUS = ATRASADO\n"
                        "TITLE_PREFIX = [AQUI]\n\n"
                        "METRICS:\n"
                        "LEAD_TIME, RISK_SCORE\n\n"
                        "LIMIT:\n"
                        "100"
                    ),
                },
            }
        )
