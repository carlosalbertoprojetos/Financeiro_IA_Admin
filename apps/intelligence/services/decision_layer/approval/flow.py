from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from apps.intelligence.services.decision_layer.guards.rules import validate_action
from apps.intelligence.services.decision_layer.models import DecisionStatus


def request_approval(
    decision: dict[str, Any],
    action: dict[str, Any],
    *,
    requested_by: str = "system",
) -> dict[str, Any]:
    """Mark action as pending human approval."""
    guard = validate_action(action)
    return {
        "status": "PENDING_APPROVAL",
        "decision_id": decision.get("id", decision.get("decision_id", "")),
        "action_type": action.get("action_type"),
        "requires_approval": True,
        "guard": guard,
        "requested_by": requested_by,
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "message": guard.get("reason") or "Action requires human approval",
    }


def approve_action(
    decision: dict[str, Any],
    *,
    action_index: int = 0,
    approved_by: str,
) -> dict[str, Any]:
    """Record human approval for a pending action."""
    actions = decision.get("recommended_actions") or []
    if action_index >= len(actions):
        return {"approved": False, "reason": "Invalid action index"}

    action = actions[action_index]
    guard = validate_action({**action, "execution_mode": "SEMI_AUTOMATIC"})
    if guard.get("blocked_by") == "bulk_limit":
        return {"approved": False, "reason": guard["reason"], "guard": guard}

    return {
        "approved": True,
        "decision_id": decision.get("id", decision.get("decision_id", "")),
        "action_type": action.get("action_type"),
        "approved_by": approved_by,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "guard": guard,
        "decision_status": DecisionStatus.IN_PROGRESS.value,
    }


def reject_action(
    decision: dict[str, Any],
    *,
    action_index: int = 0,
    rejected_by: str,
    reason: str = "",
) -> dict[str, Any]:
    actions = decision.get("recommended_actions") or []
    action_type = actions[action_index].get("action_type") if action_index < len(actions) else "unknown"
    return {
        "approved": False,
        "decision_id": decision.get("id", decision.get("decision_id", "")),
        "action_type": action_type,
        "rejected_by": rejected_by,
        "rejected_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason or "Rejected by operator",
        "decision_status": DecisionStatus.REJECTED.value,
    }
