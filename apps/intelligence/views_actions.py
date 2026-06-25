from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.intelligence.services.decision_layer.approval.flow import approve_action, reject_action
from apps.intelligence.services.decision_layer.guards.rules import is_auto_execution_enabled
from apps.intelligence.services.decision_layer.orchestrator import execute_decision_action
from apps.intelligence.services.decision_layer.pipeline import enrich_with_decisions
from apps.intelligence.services.decision_layer.queue.manager import get_pending_queue, load_decision
from apps.intelligence.services.pilot.feedback import capture_rejection, record_decision_feedback


class ActionsOverviewView(APIView):
    def get(self, request: Request) -> Response:
        return Response({
            "endpoints": {
                "queue": "GET /api/actions/queue/",
                "generate": "POST /api/actions/generate/",
                "execute": "POST /api/actions/execute/",
                "approve": "POST /api/actions/approve/",
                "reject": "POST /api/actions/reject/",
                "decision": "GET /api/actions/decisions/{decision_id}/",
            },
            "auto_execution": is_auto_execution_enabled(),
            "auto_execution_env": "DAL_AUTO_EXECUTION=true",
        })


class ActionQueueView(APIView):
    def get(self, request: Request) -> Response:
        board_id = str(request.query_params.get("board_id", ""))
        limit = int(request.query_params.get("limit", 50))
        queue = get_pending_queue(board_id=board_id, limit=limit)
        return Response({"queue": queue, "count": len(queue)})


class GenerateDecisionsView(APIView):
    def post(self, request: Request) -> Response:
        data = request.data or {}
        output = data.get("output")
        if not output:
            return Response({"error": "output required"}, status=status.HTTP_400_BAD_REQUEST)
        trace_id = str(data.get("trace_id", ""))
        persist = bool(data.get("persist", False))
        enriched = enrich_with_decisions(
            output,
            source_trace_id=trace_id,
            owner=str(data.get("owner", "api")),
            persist=persist,
        )
        return Response({
            "decisions": enriched.get("decisions", []),
            "action_queue": enriched.get("action_queue", []),
            "decision_summary": enriched.get("decision_summary", {}),
        })


class ExecuteActionView(APIView):
    def post(self, request: Request) -> Response:
        data = request.data or {}
        decision_id = str(data.get("decision_id", ""))
        if not decision_id:
            return Response({"error": "decision_id required"}, status=status.HTTP_400_BAD_REQUEST)
        result = execute_decision_action(
            decision_id,
            action_index=int(data.get("action_index", 0)),
            approved_by=str(data.get("approved_by", "")),
            user_id=str(getattr(request.user, "username", None) or data.get("user_id", "api")),
            dry_run=bool(data.get("dry_run", False)),
        )
        if result.get("status") == "PENDING_APPROVAL":
            return Response(result, status=status.HTTP_202_ACCEPTED)
        if result.get("status") in ("BLOCKED", "APPROVAL_DENIED"):
            return Response(result, status=status.HTTP_403_FORBIDDEN)
        return Response(result)


class ApproveActionView(APIView):
    def post(self, request: Request) -> Response:
        data = request.data or {}
        decision_id = str(data.get("decision_id", ""))
        approved_by = str(data.get("approved_by", getattr(request.user, "username", "") or "operator"))
        decision = load_decision(decision_id)
        if not decision:
            return Response({"error": "Decision not found"}, status=status.HTTP_404_NOT_FOUND)
        approval = approve_action(decision, action_index=int(data.get("action_index", 0)), approved_by=approved_by)
        if not approval.get("approved"):
            return Response(approval, status=status.HTTP_403_FORBIDDEN)
        result = execute_decision_action(
            decision_id,
            action_index=int(data.get("action_index", 0)),
            approved_by=approved_by,
            dry_run=bool(data.get("dry_run", False)),
        )
        return Response({"approval": approval, "execution": result})


class RejectActionView(APIView):
    def post(self, request: Request) -> Response:
        data = request.data or {}
        decision_id = str(data.get("decision_id", ""))
        decision = load_decision(decision_id)
        if not decision:
            return Response({"error": "Decision not found"}, status=status.HTTP_404_NOT_FOUND)
        result = reject_action(
            decision,
            action_index=int(data.get("action_index", 0)),
            rejected_by=str(data.get("rejected_by", "operator")),
            reason=str(data.get("reason", "")),
        )
        actions = decision.get("recommended_actions") or []
        action_index = int(data.get("action_index", 0))
        action = actions[action_index] if action_index < len(actions) else {}
        capture_rejection(
            decision_id=decision_id,
            operator=str(data.get("rejected_by", "operator")),
            reason=str(data.get("reason", "")),
            action=action,
        )
        return Response(result)


class DecisionDetailView(APIView):
    def get(self, request: Request, decision_id: str) -> Response:
        decision = load_decision(decision_id)
        if not decision:
            return Response({"error": "Decision not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"decision": decision})
