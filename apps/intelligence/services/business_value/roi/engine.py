from __future__ import annotations

from typing import Any

from apps.intelligence.services.business_value.config import action_cost_brl


def compute_action_roi(
    *,
    action_type: str,
    avoided_loss: float,
    realized_benefit: float = 0,
    action_cost: float | None = None,
) -> dict[str, Any]:
    """
    ROI = ((avoided_loss + realized_benefit) - cost) / cost * 100
    All inputs must be traceable — cost from config, benefits from measured outcomes.
    """
    cost = action_cost if action_cost is not None else action_cost_brl(action_type)
    total_benefit = avoided_loss + realized_benefit
    net = total_benefit - cost
    roi_pct = round((net / cost) * 100, 1) if cost > 0 else 0.0

    return {
        "action_type": action_type,
        "action_cost": round(cost, 2),
        "avoided_loss": round(avoided_loss, 2),
        "realized_benefit": round(realized_benefit, 2),
        "total_benefit": round(total_benefit, 2),
        "net_value": round(net, 2),
        "roi_pct": roi_pct,
        "confidence_score": 0.85 if avoided_loss > 0 else 0.5,
        "formula": "roi_pct = (total_benefit - cost) / cost * 100",
    }
