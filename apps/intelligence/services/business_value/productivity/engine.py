from __future__ import annotations

from typing import Any

from apps.intelligence.services.business_value.config import hourly_rate_brl


def compute_productivity_value(
    *,
    risk_before: float,
    risk_after: float,
    execution_time_ms: int = 0,
    hours_per_risk_point: float = 0.1,
) -> dict[str, Any]:
    """
    Productivity value from measurable risk reduction and execution time.
    hours_saved = risk_reduction * hours_per_risk_point (configurable proxy from observed risk delta)
    """
    risk_reduction = max(0, risk_before - risk_after)
    hours_saved = risk_reduction * hours_per_risk_point
    hours_recovered = max(0, (execution_time_ms / 3_600_000) * 0)  # execution is cost not recovery
    capacity_hours = hours_saved
    throughput_gain = round(hours_saved / 8, 2) if hours_saved else 0  # workdays equivalent

    value_brl = hours_saved * hourly_rate_brl()
    confidence = 0.75 if risk_before > 0 and risk_after >= 0 else 0.4

    return {
        "hours_saved": round(hours_saved, 2),
        "hours_recovered": round(hours_recovered, 2),
        "capacity_hours_freed": round(capacity_hours, 2),
        "throughput_gain_days": throughput_gain,
        "estimated_benefit": round(value_brl, 2),
        "confidence_score": confidence,
        "inputs": {
            "risk_before": risk_before,
            "risk_after": risk_after,
            "risk_reduction": risk_reduction,
            "hourly_rate": hourly_rate_brl(),
        },
    }
