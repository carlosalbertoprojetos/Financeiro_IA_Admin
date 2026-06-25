from __future__ import annotations

import logging
import uuid
from datetime import timedelta
from typing import Any

from django.utils import timezone

from apps.intelligence.models import ActionExecutionLog
from apps.intelligence.services.decision_layer.approval.flow import approve_action, request_approval
from apps.intelligence.services.decision_layer.feedback.loop import measure_action_impact, record_feedback
from apps.intelligence.services.decision_layer.guards.rules import validate_action
from apps.intelligence.services.decision_layer.models import DecisionStatus
from apps.intelligence.services.decision_layer.queue.manager import mark_executed, mark_failed, mark_in_progress
from apps.intelligence.services.decision_layer.trello_executor import TrelloActionExecutor
from apps.intelligence.services.observability.context import get_collector
from apps.intelligence.services.risk_engine.scorer import assess_card_risk
from integrations.trello.models import Card

logger = logging.getLogger(__name__)


class ActionOrchestrator:
    """Execute structured actions via Trello, internal systems, or webhooks."""

    def __init__(self, *, dry_run: bool = False) -> None:
        self.dry_run = dry_run
        self._trello = TrelloActionExecutor(dry_run=dry_run)

    def execute_action(
        self,
        decision: dict[str, Any],
        action: dict[str, Any],
        *,
        action_index: int = 0,
        approved_by: str = "",
        user_id: str = "system",
        trace_id: str = "",
    ) -> dict[str, Any]:
        decision_id = decision.get("id", decision.get("decision_id", ""))
        action_type = action.get("action_type", "")
        execution_mode = action.get("execution_mode", "MANUAL")
        trace_id = trace_id or decision.get("source_trace_id", "")

        recent = _recent_executions(action.get("target_card_id", ""))
        auto_count = _auto_count_last_hour()
        guard = validate_action(action, recent_executions=recent, auto_count_last_hour=auto_count)

        if guard.get("requires_approval") and not approved_by:
            approval = request_approval(decision, action, requested_by=user_id)
            _log_execution(decision_id, action, trace_id, "PENDING_APPROVAL", approval, user_id)
            _record_action_trace(decision_id, action_type, trace_id, "pending_approval", approval)
            return {"status": "PENDING_APPROVAL", "approval": approval, "guard": guard}

        if not guard.get("allowed"):
            _log_execution(decision_id, action, trace_id, "BLOCKED", guard, user_id)
            return {"status": "BLOCKED", "guard": guard}

        if execution_mode == "MANUAL" and not approved_by:
            _record_action_trace(decision_id, action_type, trace_id, "suggested", {"mode": "MANUAL"})
            return {"status": "SUGGESTED", "action": action, "message": "Manual action — execution not attempted"}

        mark_in_progress(decision_id)
        before_state = _capture_card_state(action.get("target_card_id", ""))

        try:
            result = self._dispatch(action)
            after_state = _capture_card_state(action.get("target_card_id", ""))
            impact = measure_action_impact(before=before_state, after=after_state, action_type=action_type)
            feedback = record_feedback(decision_id, impact, trace_id=trace_id)

            from apps.intelligence.services.organizational_learning.pipeline import record_action_learning
            category = (decision.get("context") or {}).get("entity", {}).get("category", "")
            if not category:
                category = (decision.get("context") or {}).get("entity", {}).get("entity_type", "GENERAL")
            learning = record_action_learning(
                decision_id=decision_id,
                action_type=action_type,
                before=before_state,
                after=after_state,
                impact=impact,
                execution_time_ms=0,
                board_id=decision.get("board_id", ""),
                category=category,
                owner=approved_by or user_id,
                context={"insight": decision.get("insight", ""), "trace_id": trace_id},
            )

            from apps.intelligence.services.business_value.pipeline import record_action_value
            value = record_action_value(
                decision_id=decision_id,
                action_type=action_type,
                before=before_state,
                after=after_state,
                effectiveness=learning.to_dict() if learning else None,
                board_id=decision.get("board_id", ""),
                category=category,
                team=(decision.get("context") or {}).get("entity", {}).get("team", ""),
                card_id=action.get("target_card_id", ""),
            )

            history_entry = {
                "action_type": action_type,
                "execution_mode": execution_mode,
                "result": result,
                "impact": impact,
                "approved_by": approved_by,
                "trace_id": trace_id,
                "execution_id": str(uuid.uuid4()),
            }
            mark_executed(decision_id, history_entry)
            _log_execution(decision_id, action, trace_id, "EXECUTED", {**result, "impact": impact, "target_card_id": action.get("target_card_id", "")}, user_id, approved_by)
            _record_action_trace(decision_id, action_type, trace_id, "executed", history_entry)

            from apps.intelligence.services.pilot.impact_tracker import schedule_impact_followups
            log_entry = ActionExecutionLog.objects.filter(
                decision_id=decision_id, status="EXECUTED",
            ).order_by("-created_at").first()
            schedule_impact_followups(
                decision_id=decision_id,
                action_type=action_type,
                board_id=decision.get("board_id", ""),
                card_id=action.get("target_card_id", ""),
                baseline=before_state,
                execution_log_id=log_entry.id if log_entry else None,
            )

            if approved_by:
                from apps.intelligence.services.pilot.feedback import capture_acceptance
                capture_acceptance(
                    decision_id=decision_id,
                    operator=approved_by,
                    action=action,
                )

            return {
                "status": "EXECUTED",
                "result": result,
                "impact": impact,
                "feedback": feedback,
                "learning": learning.to_dict() if learning else None,
                "value": value.to_dict() if value else None,
                "trace_id": trace_id,
                "decision_id": decision_id,
            }
        except Exception as exc:
            logger.exception("Action execution failed: %s", action_type)
            retry_result = mark_failed(decision_id, str(exc))
            _log_execution(decision_id, action, trace_id, "FAILED", {"error": str(exc)}, user_id)
            _record_action_trace(decision_id, action_type, trace_id, "failed", {"error": str(exc)})
            return {"status": "FAILED", "error": str(exc), "retry": retry_result}


    def _dispatch(self, action: dict[str, Any]) -> dict[str, Any]:
        action_type = action.get("action_type", "")
        if action_type in ("ADD_COMMENT", "REOPEN_CARD", "ADJUST_PRIORITY", "REASSIGN_OWNER", "MOVE_CARD", "ESCALATE_TASK"):
            return self._trello.execute(action)
        if action_type == "CREATE_ALERT":
            return {"channel": "internal", "alert_created": True, "params": action.get("params", {})}
        if action_type == "WEBHOOK_NOTIFY":
            return {"channel": "webhook", "dispatched": not self.dry_run, "params": action.get("params", {})}
        if action_type == "MANAGERIAL_INTERVENTION":
            return {"channel": "suggestion", "executed": False, "params": action.get("params", {})}
        raise ValueError(f"Unknown action type: {action_type}")


def execute_decision_action(
    decision_id: str,
    *,
    action_index: int = 0,
    approved_by: str = "",
    user_id: str = "system",
    dry_run: bool = False,
) -> dict[str, Any]:
    from apps.intelligence.services.decision_layer.queue.manager import load_decision

    decision = load_decision(decision_id)
    if not decision:
        return {"status": "NOT_FOUND", "decision_id": decision_id}

    actions = decision.get("recommended_actions") or []
    if action_index >= len(actions):
        return {"status": "INVALID_ACTION_INDEX", "decision_id": decision_id}

    if approved_by:
        approval = approve_action(decision, action_index=action_index, approved_by=approved_by)
        if not approval.get("approved"):
            return {"status": "APPROVAL_DENIED", **approval}

    orchestrator = ActionOrchestrator(dry_run=dry_run)
    return orchestrator.execute_action(
        decision,
        actions[action_index],
        action_index=action_index,
        approved_by=approved_by,
        user_id=user_id,
        trace_id=decision.get("source_trace_id", ""),
    )


def _capture_card_state(card_id: str) -> dict[str, Any]:
    if not card_id:
        return {}
    card = Card.objects.filter(trello_id=card_id).first()
    if not card:
        return {"card_id": card_id}
    assessment = assess_card_risk(card)
    return {
        "card_id": card_id,
        "risk_score": assessment.score,
        "sla_breach_probability": assessment.score,
        "status": "COMPLETED" if card.is_closed else "OPEN",
        "title": card.title,
    }


def _recent_executions(card_id: str) -> list[dict[str, Any]]:
    if not card_id:
        return []
    cutoff = timezone.now() - timedelta(seconds=300)
    logs = ActionExecutionLog.objects.filter(
        target_card_id=card_id,
        created_at__gte=cutoff,
    ).order_by("-created_at")[:5]
    return [
        {"action_type": log.action_type, "target_card_id": log.target_card_id, "within_cooldown": True}
        for log in logs
    ]


def _auto_count_last_hour() -> int:
    cutoff = timezone.now() - timedelta(hours=1)
    return ActionExecutionLog.objects.filter(
        execution_mode="AUTOMATIC",
        status="EXECUTED",
        created_at__gte=cutoff,
    ).count()


def _log_execution(
    decision_id: str,
    action: dict[str, Any],
    trace_id: str,
    status: str,
    result: dict[str, Any],
    user_id: str,
    approved_by: str = "",
) -> None:
    action_type = action.get("action_type", "")
    try:
        ActionExecutionLog.objects.create(
            decision_id=decision_id,
            action_type=action_type,
            execution_mode=action.get("execution_mode", "MANUAL"),
            trace_id=trace_id,
            status=status,
            result_json=result,
            user_id=user_id,
            approved_by=approved_by,
            target_card_id=result.get("target_card_id", action.get("target_card_id", "")),
        )
    except Exception:
        logger.exception("Failed to log action execution")


def _record_action_trace(decision_id: str, action_type: str, trace_id: str, effect: str, meta: dict[str, Any]) -> None:
    collector = get_collector()
    if collector and hasattr(collector, "record_action"):
        collector.record_action(decision_id, action_type, trace_id, effect, meta)
