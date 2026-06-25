from __future__ import annotations

from typing import Any

OUTCOME_SUCCESS = "SUCCESS"
OUTCOME_LOW_IMPACT = "LOW_IMPACT"
OUTCOME_FAILURE = "FAILURE"
OUTCOME_NEUTRAL = "NEUTRAL"


def evaluate_action_outcome(
    *,
    action_type: str,
    before: dict[str, Any],
    after: dict[str, Any],
    impact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Evaluate executed action result from real before/after measurements.
    No AI inference — only computed deltas from observed data.
    """
    impact = impact or {}
    risk_before = float(before.get("risk_score", 0) or 0)
    risk_after = float(after.get("risk_score", 0) or 0)
    sla_before = float(before.get("sla_breach_probability", before.get("risk_score", 0)) or 0)
    sla_after = float(after.get("sla_breach_probability", after.get("risk_score", 0)) or 0)

    risk_delta = risk_after - risk_before
    sla_delta = sla_after - sla_before
    risk_reduction_pct = ((risk_before - risk_after) / risk_before * 100) if risk_before > 0 else 0.0
    sla_improvement_pct = ((sla_before - sla_after) / sla_before * 100) if sla_before > 0 else 0.0

    label = _classify_outcome(action_type, risk_delta, sla_delta, impact)

    return {
        "action_type": action_type,
        "outcome_label": label,
        "risk_before": risk_before,
        "risk_after": risk_after,
        "risk_delta": round(risk_delta, 2),
        "risk_reduction_pct": round(risk_reduction_pct, 2),
        "sla_before": sla_before,
        "sla_after": sla_after,
        "sla_delta": round(sla_delta, 2),
        "sla_improvement_pct": round(sla_improvement_pct, 2),
        "problem_resolved": impact.get("problem_resolved", False),
    }


def _classify_outcome(
    action_type: str,
    risk_delta: float,
    sla_delta: float,
    impact: dict[str, Any],
) -> str:
    if action_type == "CREATE_ALERT":
        return OUTCOME_NEUTRAL

    if risk_delta > 5 or sla_delta > 5:
        return OUTCOME_FAILURE

    if impact.get("problem_resolved") and risk_delta <= -10:
        return OUTCOME_SUCCESS

    if risk_delta <= -15 or (risk_delta < 0 and sla_delta <= -10):
        return OUTCOME_SUCCESS

    if abs(risk_delta) < 5 and abs(sla_delta) < 5:
        return OUTCOME_LOW_IMPACT

    if risk_delta < 0 or sla_delta < 0:
        return OUTCOME_SUCCESS

    return OUTCOME_LOW_IMPACT
