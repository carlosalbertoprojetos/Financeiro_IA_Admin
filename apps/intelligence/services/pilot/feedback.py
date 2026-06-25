from __future__ import annotations

from typing import Any

from apps.intelligence.models import DecisionFeedbackRecord
from apps.intelligence.services.decision_layer.queue.manager import load_decision, mark_rejected


def record_decision_feedback(
    *,
    decision_id: str,
    disposition: str,
    operator: str = "operator",
    reason: str = "",
    original_action: dict[str, Any] | None = None,
    final_action: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> DecisionFeedbackRecord:
    """Persist human decision quality feedback for POCL evaluation."""
    decision = load_decision(decision_id) or {}
    actions = decision.get("recommended_actions") or []
    action = original_action or (actions[0] if actions else {})
    board_id = decision.get("board_id", "")

    record = DecisionFeedbackRecord.objects.create(
        decision_id=decision_id,
        board_id=board_id,
        action_type=action.get("action_type", ""),
        disposition=disposition,
        operator=operator,
        original_action_json=action,
        final_action_json=final_action or action,
        reason=reason,
        context_json=context or {},
    )

    if disposition == DecisionFeedbackRecord.Disposition.IGNORED:
        mark_rejected(decision_id, reason or "Ignored by operator", rejected_by=operator)

    return record


def capture_acceptance(
    *,
    decision_id: str,
    operator: str,
    action: dict[str, Any] | None = None,
    modified: bool = False,
    reason: str = "",
) -> DecisionFeedbackRecord:
    disposition = (
        DecisionFeedbackRecord.Disposition.MODIFIED
        if modified
        else DecisionFeedbackRecord.Disposition.ACCEPTED
    )
    return record_decision_feedback(
        decision_id=decision_id,
        disposition=disposition,
        operator=operator,
        reason=reason,
        original_action=action,
        final_action=action,
        context={"source": "approval_flow"},
    )


def capture_rejection(
    *,
    decision_id: str,
    operator: str,
    reason: str = "",
    action: dict[str, Any] | None = None,
) -> DecisionFeedbackRecord:
    return record_decision_feedback(
        decision_id=decision_id,
        disposition=DecisionFeedbackRecord.Disposition.IGNORED,
        operator=operator,
        reason=reason,
        original_action=action,
        context={"source": "approval_flow"},
    )
