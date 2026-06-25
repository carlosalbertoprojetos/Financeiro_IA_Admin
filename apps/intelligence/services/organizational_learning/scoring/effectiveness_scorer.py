from __future__ import annotations

from typing import Any

from apps.intelligence.services.organizational_learning.outcomes.evaluator import (
    OUTCOME_FAILURE,
    OUTCOME_LOW_IMPACT,
    OUTCOME_NEUTRAL,
    OUTCOME_SUCCESS,
)


def compute_effectiveness_score(
    outcome: dict[str, Any],
    *,
    execution_time_ms: int = 0,
    bottleneck_resolved: bool = False,
) -> tuple[float, float]:
    """
    Compute outcome_score (0-100) and effectiveness_score (0-100) from real measurements.
    Returns (outcome_score, effectiveness_score).
    """
    label = outcome.get("outcome_label", OUTCOME_NEUTRAL)
    risk_pct = max(0.0, outcome.get("risk_reduction_pct", 0))
    sla_pct = max(0.0, outcome.get("sla_improvement_pct", 0))

    if label == OUTCOME_FAILURE:
        outcome_score = max(0.0, 20.0 - abs(outcome.get("risk_delta", 0)))
        effectiveness_score = outcome_score * 0.5
        return round(outcome_score, 2), round(effectiveness_score, 2)

    if label == OUTCOME_NEUTRAL:
        return 50.0, 50.0

    if label == OUTCOME_LOW_IMPACT:
        outcome_score = 30.0 + min(20.0, risk_pct * 0.5 + sla_pct * 0.3)
        effectiveness_score = outcome_score
        return round(outcome_score, 2), round(effectiveness_score, 2)

    # SUCCESS
    risk_component = min(40.0, risk_pct * 0.8)
    sla_component = min(30.0, sla_pct * 0.6)
    resolution_bonus = 20.0 if outcome.get("problem_resolved") else 0.0
    bottleneck_bonus = 10.0 if bottleneck_resolved else 0.0

    outcome_score = min(100.0, risk_component + sla_component + resolution_bonus + bottleneck_bonus)

    time_penalty = 0.0
    if execution_time_ms > 86_400_000:
        time_penalty = 10.0
    elif execution_time_ms > 3_600_000:
        time_penalty = 5.0

    effectiveness_score = max(0.0, outcome_score - time_penalty)
    return round(outcome_score, 2), round(effectiveness_score, 2)
