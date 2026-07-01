from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.intelligence.services.product_readiness.connectors import connector_readiness
from apps.intelligence.services.product_readiness.demo import executive_demo_payload
from apps.intelligence.services.product_readiness.diagnostics import (
    multi_tenant_audit,
    self_diagnostics,
    system_health,
)
from apps.intelligence.services.product_readiness.licensing import check_plan_limits, plan_catalog, require_plan_feature
from apps.intelligence.services.product_readiness.marketplace import marketplace_catalog
from apps.intelligence.services.product_readiness.onboarding import onboarding_blueprint
from apps.intelligence.services.product_readiness.onboarding_state import (
    get_or_create_state,
    mark_first_report,
    mark_initial_sync,
    mark_token_validated,
    select_boards,
    serialize_state,
    set_discovered_boards,
)
from apps.intelligence.services.product_readiness.tenant_access import get_request_tenant
from apps.intelligence.services.product_readiness.usage import (
    customer_success_dashboard,
    usage_analytics,
)
from apps.intelligence.services.product_readiness.workspace import validate_workspace


class SystemHealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request) -> Response:
        payload = system_health()
        status_code = 200 if payload["status"] in ("ok", "degraded") else 503
        return Response(payload, status=status_code)


class WorkspaceValidationView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request) -> Response:
        payload = validate_workspace()
        status_code = 200 if payload["status"] == "ready" else 503
        return Response(payload, status=status_code)


class SelfDiagnosticsView(APIView):
    def get(self, request: Request) -> Response:
        return Response(self_diagnostics())


class UsageAnalyticsView(APIView):
    def get(self, request: Request) -> Response:
        tenant = get_request_tenant(request)
        return Response(usage_analytics(board_id=str(request.query_params.get("board_id", "")), tenant=tenant))


class CustomerSuccessDashboardView(APIView):
    def get(self, request: Request) -> Response:
        tenant = get_request_tenant(request)
        return Response(customer_success_dashboard(board_id=str(request.query_params.get("board_id", "")), tenant=tenant))


class LicensingView(APIView):
    def get(self, request: Request) -> Response:
        return Response(plan_catalog())


class ConnectorFrameworkView(APIView):
    def get(self, request: Request) -> Response:
        return Response(connector_readiness())


class MarketplaceView(APIView):
    def get(self, request: Request) -> Response:
        tenant = get_request_tenant(request)
        require_plan_feature(tenant, "marketplace")
        return Response(marketplace_catalog())


class DemoModeView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request) -> Response:
        return Response(executive_demo_payload())


class OnboardingView(APIView):
    def get(self, request: Request) -> Response:
        return Response(onboarding_blueprint())


class OnboardingStateView(APIView):
    def get(self, request: Request) -> Response:
        tenant = get_request_tenant(request)
        return Response(serialize_state(get_or_create_state(tenant)))


class OnboardingTokenView(APIView):
    def post(self, request: Request) -> Response:
        tenant = get_request_tenant(request)
        token = str(request.data.get("api_token", "")).strip()
        api_key = str(request.data.get("api_key", "")).strip()
        state = get_or_create_state(tenant)
        valid = bool(token and api_key)
        error = "" if valid else "api_key and api_token are required"
        return Response(serialize_state(mark_token_validated(state, valid=valid, error=error)), status=200 if valid else 400)


class OnboardingDiscoverBoardsView(APIView):
    def post(self, request: Request) -> Response:
        tenant = get_request_tenant(request)
        state = get_or_create_state(tenant)
        boards = request.data.get("boards")
        if boards is None:
            boards = [
                {"id": board.trello_id, "name": board.name}
                for board in tenant.trello_boards.filter(closed=False).order_by("name")[:50]
            ]
        return Response(serialize_state(set_discovered_boards(state, boards)))


class OnboardingSelectBoardsView(APIView):
    def post(self, request: Request) -> Response:
        tenant = get_request_tenant(request)
        state = get_or_create_state(tenant)
        board_ids = request.data.get("board_ids") or []
        available = set(tenant.trello_boards.values_list("trello_id", flat=True))
        selected = [board_id for board_id in board_ids if board_id in available]
        if len(selected) != len(board_ids):
            state.errors_json = [*state.errors_json, {"step": "board_selection", "error": "one or more boards are outside tenant scope"}]
            state.save()
            return Response(serialize_state(state), status=403)
        limit = check_plan_limits(tenant, boards=len(selected))
        if not limit["allowed"]:
            state.errors_json = [*state.errors_json, {"step": "board_selection", "error": "plan limit exceeded", "detail": limit}]
            state.save()
            return Response({"error": "plan limit exceeded", "detail": limit, "state": serialize_state(state)}, status=402)
        return Response(serialize_state(select_boards(state, selected)))


class OnboardingSyncView(APIView):
    def post(self, request: Request) -> Response:
        tenant = get_request_tenant(request)
        state = get_or_create_state(tenant)
        if not state.boards_selected:
            return Response(
                serialize_state(mark_initial_sync(state, completed=False, error="select boards before sync")),
                status=400,
            )
        return Response(serialize_state(mark_initial_sync(state, completed=True)))


class OnboardingFirstReportView(APIView):
    def post(self, request: Request) -> Response:
        tenant = get_request_tenant(request)
        state = get_or_create_state(tenant)
        if not state.initial_sync_completed:
            return Response(serialize_state(state), status=400)
        return Response(serialize_state(mark_first_report(state)))


class MultiTenantAuditView(APIView):
    def get(self, request: Request) -> Response:
        return Response(multi_tenant_audit())
