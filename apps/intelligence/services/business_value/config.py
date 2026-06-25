from __future__ import annotations

import os


def hourly_rate_brl() -> float:
    try:
        return float(os.environ.get("BVE_HOURLY_RATE_BRL", "150"))
    except ValueError:
        return 150.0


def base_impact_brl() -> float:
    """Base financial impact per high-risk event — configurable, not per-action invented."""
    try:
        return float(os.environ.get("BVE_BASE_IMPACT_BRL", "20000"))
    except ValueError:
        return 20000.0


def action_cost_brl(action_type: str) -> float:
    """Configurable action execution costs."""
    key = f"BVE_ACTION_COST_{action_type}"
    raw = os.environ.get(key)
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    defaults = {
        "ESCALATE_TASK": 200.0,
        "REASSIGN_OWNER": 150.0,
        "CREATE_ALERT": 50.0,
        "ADJUST_PRIORITY": 100.0,
        "MANAGERIAL_INTERVENTION": 300.0,
        "ADD_COMMENT": 30.0,
        "REOPEN_CARD": 120.0,
        "MOVE_CARD": 80.0,
    }
    return defaults.get(action_type, 100.0)


def hours_per_workday() -> float:
    try:
        return float(os.environ.get("BVE_HOURS_PER_WORKDAY", "8"))
    except ValueError:
        return 8.0
