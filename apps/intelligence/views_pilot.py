from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.intelligence.models import (
    ActionExecutionLog,
    ActionImpactFollowUp,
    BusinessValueRecordModel,
    DecisionFeedbackRecord,
    DecisionRecord,
    ReportAuditLog,
)
from apps.intelligence.services.pilot.config import activate_pilot, pilot_status_summary
from apps.intelligence.services.pilot.daily_cycle import run_daily_cycle
from apps.intelligence.services.pilot.decision_stream import run_decision_stream
from apps.intelligence.services.pilot.evaluation import compute_pilot_metrics, generate_pilot_evaluation_report
from apps.intelligence.services.pilot.feedback import record_decision_feedback
from apps.intelligence.services.pilot.impact_tracker import process_due_followups
from apps.intelligence.services.pilot.report_generator import generate_executive_daily_report
from apps.intelligence.services.pilot.config import get_active_pilot


class PilotStatusView(APIView):
    def get(self, request: Request) -> Response:
        board_id = str(request.query_params.get("board_id", ""))
        metrics = compute_pilot_metrics(board_id=board_id) if board_id else {}
        return Response({
            **pilot_status_summary(board_id=board_id),
            "metrics": metrics,
            "endpoints": {
                "activate": "POST /api/pilot/activate/",
                "stream": "POST /api/pilot/stream/",
                "cycle": "POST /api/pilot/cycle/",
                "feedback": "POST /api/pilot/feedback/",
                "followups": "POST /api/pilot/followups/",
                "report": "POST /api/pilot/report/",
                "evaluate": "GET /api/pilot/evaluate/",
            },
        })


class PilotActivateView(APIView):
    def post(self, request: Request) -> Response:
        data = request.data or {}
        board_id = str(data.get("board_id", ""))
        team_name = str(data.get("team_name", ""))
        if not board_id or not team_name:
            return Response({"error": "board_id and team_name required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            pilot = activate_pilot(
                board_id=board_id,
                team_name=team_name,
                board_name=str(data.get("board_name", "")),
                duration_days=int(data.get("duration_days", 10)),
            )
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        return Response({"pilot_id": pilot.id, "board_id": pilot.board_id, "status": pilot.status})


class PilotDecisionStreamView(APIView):
    def post(self, request: Request) -> Response:
        data = request.data or {}
        board_id = str(data.get("board_id", ""))
        if not board_id:
            return Response({"error": "board_id required"}, status=status.HTTP_400_BAD_REQUEST)
        result = run_decision_stream(
            board_id,
            trigger=str(data.get("trigger", "api")),
            limit=int(data.get("limit", 20)),
        )
        return Response(result)


class PilotDailyCycleView(APIView):
    def post(self, request: Request) -> Response:
        data = request.data or {}
        board_id = str(data.get("board_id", ""))
        phase = str(data.get("phase", "morning"))
        if not board_id:
            return Response({"error": "board_id required"}, status=status.HTTP_400_BAD_REQUEST)
        result = run_daily_cycle(
            board_id,
            phase=phase,
            trigger="api",
            sync=bool(data.get("sync", True)),
        )
        return Response(result)


class PilotFeedbackView(APIView):
    def post(self, request: Request) -> Response:
        data = request.data or {}
        decision_id = str(data.get("decision_id", ""))
        disposition = str(data.get("disposition", "")).upper()
        if not decision_id or disposition not in ("ACCEPTED", "IGNORED", "MODIFIED"):
            return Response(
                {"error": "decision_id and disposition (ACCEPTED|IGNORED|MODIFIED) required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        record = record_decision_feedback(
            decision_id=decision_id,
            disposition=disposition,
            operator=str(data.get("operator", "operator")),
            reason=str(data.get("reason", "")),
            original_action=data.get("original_action"),
            final_action=data.get("final_action"),
            context=data.get("context"),
        )
        return Response({"feedback_id": record.id, "disposition": record.disposition})


class PilotFollowupsView(APIView):
    def post(self, request: Request) -> Response:
        board_id = str((request.data or {}).get("board_id", ""))
        result = process_due_followups(board_id=board_id)
        return Response(result)


class PilotReportView(APIView):
    def post(self, request: Request) -> Response:
        data = request.data or {}
        board_id = str(data.get("board_id", ""))
        if not board_id:
            return Response({"error": "board_id required"}, status=status.HTTP_400_BAD_REQUEST)
        pilot = get_active_pilot(board_id=board_id)
        path = generate_executive_daily_report(
            board_id=board_id,
            pilot=pilot,
            output_path=str(data.get("output_path", "")),
        )
        return Response({"report_path": path})


class PilotEvaluateView(APIView):
    def get(self, request: Request) -> Response:
        board_id = str(request.query_params.get("board_id", ""))
        if not board_id:
            return Response({"error": "board_id required"}, status=status.HTTP_400_BAD_REQUEST)
        metrics = compute_pilot_metrics(board_id=board_id)
        report_path = generate_pilot_evaluation_report(board_id=board_id)
        return Response({"metrics": metrics, "evaluation_report": report_path})


class PilotDashboardView(APIView):
    def get(self, request: Request) -> Response:
        board_id = str(request.query_params.get("board_id", ""))
        if not board_id:
            return Response({"error": "board_id required"}, status=status.HTTP_400_BAD_REQUEST)

        reports = ReportAuditLog.objects.filter(board_id=board_id)
        decisions = DecisionRecord.objects.filter(board_id=board_id)
        feedback = DecisionFeedbackRecord.objects.filter(board_id=board_id)
        executions = ActionExecutionLog.objects.filter(decision_id__in=decisions.values("decision_id"))
        followups = ActionImpactFollowUp.objects.filter(board_id=board_id)
        value_records = BusinessValueRecordModel.objects.filter(board_id=board_id)

        accepted = feedback.filter(disposition=DecisionFeedbackRecord.Disposition.ACCEPTED).count()
        ignored = feedback.filter(disposition=DecisionFeedbackRecord.Disposition.IGNORED).count()
        modified = feedback.filter(disposition=DecisionFeedbackRecord.Disposition.MODIFIED).count()
        measured_followups = followups.filter(status=ActionImpactFollowUp.Status.MEASURED).count()
        latest_report = reports.order_by("-created_at").first()

        return Response({
            **pilot_status_summary(board_id=board_id),
            "board_id": board_id,
            "usage": {
                "reports_generated": reports.count(),
                "exports_generated": reports.exclude(export_format="json").count(),
                "last_report_at": latest_report.created_at.isoformat() if latest_report else "",
            },
            "decisions": {
                "suggested": decisions.count(),
                "accepted": accepted,
                "ignored": ignored,
                "modified": modified,
                "pending": decisions.filter(status__in=["OPEN", "PENDING_APPROVAL"]).count(),
            },
            "risks": {
                "detected": decisions.filter(priority__in=["HIGH", "ALTA", "CRITICAL", "CRITICA"]).count(),
                "top": list(decisions.order_by("-score")[:5].values("decision_id", "priority", "score", "insight")),
            },
            "impact": {
                "followups_scheduled": followups.filter(status=ActionImpactFollowUp.Status.SCHEDULED).count(),
                "followups_measured": measured_followups,
                "actions_executed": executions.filter(status="EXECUTED").count(),
                "realized_benefit": sum(item.realized_benefit for item in value_records),
                "avoided_loss": sum(item.avoided_loss for item in value_records),
            },
            "quality": {
                "latest_report_quality_score": _summary_score(latest_report, "report_quality_score"),
                "latest_decision_value_score": _summary_score(latest_report, "decision_value_score"),
            },
            "operating_mode": {
                "dal_auto_execution": "false",
                "human_approval_required": True,
                "destructive_actions_allowed": False,
                "feedback_required": True,
            },
        })


def _summary_score(report: ReportAuditLog | None, key: str) -> int | float | None:
    if not report:
        return None
    summary = report.result_summary or {}
    value = summary.get(key)
    if isinstance(value, dict):
        return value.get("score")
    return value
