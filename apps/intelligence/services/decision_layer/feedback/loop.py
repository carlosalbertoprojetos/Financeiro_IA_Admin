from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def measure_action_impact(
    *,
    before: dict[str, Any],
    after: dict[str, Any],
    action_type: str,
) -> dict[str, Any]:
    """Compare pre/post state to evaluate action effectiveness."""
    before_risk = before.get("risk_score", 0) or 0
    after_risk = after.get("risk_score", 0) or 0
    delta = after_risk - before_risk

    resolved = False
    if action_type in ("ESCALATE_TASK", "ADJUST_PRIORITY", "REASSIGN_OWNER", "MANAGERIAL_INTERVENTION"):
        resolved = after_risk < before_risk or after.get("status") != before.get("status")
    elif action_type == "CREATE_ALERT":
        resolved = True
    elif action_type == "REOPEN_CARD":
        resolved = after.get("status") == "OPEN"

    return {
        "action_type": action_type,
        "before_risk_score": before_risk,
        "after_risk_score": after_risk,
        "risk_delta": delta,
        "risk_reduced": delta < 0,
        "problem_resolved": resolved,
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "feedback_score": _feedback_score(before_risk, after_risk, resolved),
    }


def record_feedback(
    decision_id: str,
    impact: dict[str, Any],
    *,
    trace_id: str = "",
) -> dict[str, Any]:
    """Format feedback record for persistence and model retraining."""
    return {
        "decision_id": decision_id,
        "trace_id": trace_id,
        "impact": impact,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "feeds_risk_model": impact.get("risk_reduced", False),
    }


def _feedback_score(before: float, after: float, resolved: bool) -> float:
    if not before:
        return 1.0 if resolved else 0.0
    improvement = (before - after) / before
    return round(min(1.0, max(0.0, improvement + (0.2 if resolved else 0))), 2)
