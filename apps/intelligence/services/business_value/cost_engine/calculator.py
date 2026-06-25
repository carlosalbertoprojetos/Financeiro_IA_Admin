from __future__ import annotations

from datetime import datetime
from typing import Any

from django.utils import timezone

from apps.intelligence.services.business_value.config import hourly_rate_brl, hours_per_workday


def compute_delay_cost(*, days_overdue: float, assignees: int = 1) -> dict[str, Any]:
    hours = max(0, days_overdue) * hours_per_workday() * max(1, assignees)
    cost = hours * hourly_rate_brl()
    confidence = 0.85 if days_overdue > 0 else 0.5
    return {
        "value_type": "DELAY_COST",
        "estimated_cost": round(cost, 2),
        "hours_lost": round(hours, 2),
        "confidence_score": confidence,
        "inputs": {"days_overdue": days_overdue, "assignees": assignees, "hourly_rate": hourly_rate_brl()},
    }


def compute_rework_cost(*, rework_events: int = 0, hours_per_event: float = 2.0) -> dict[str, Any]:
    hours = rework_events * hours_per_event
    cost = hours * hourly_rate_brl()
    return {
        "value_type": "REWORK_COST",
        "estimated_cost": round(cost, 2),
        "hours_lost": round(hours, 2),
        "confidence_score": 0.8 if rework_events > 0 else 0.3,
        "inputs": {"rework_events": rework_events, "hours_per_event": hours_per_event},
    }


def compute_blocking_cost(*, blocked_hours: float = 0, blocked_members: int = 1) -> dict[str, Any]:
    hours = blocked_hours * max(1, blocked_members)
    cost = hours * hourly_rate_brl()
    return {
        "value_type": "BLOCKING_COST",
        "estimated_cost": round(cost, 2),
        "hours_lost": round(hours, 2),
        "confidence_score": 0.75 if blocked_hours > 0 else 0.4,
        "inputs": {"blocked_hours": blocked_hours, "blocked_members": blocked_members},
    }


def compute_waiting_cost(*, wait_hours: float = 0) -> dict[str, Any]:
    cost = wait_hours * hourly_rate_brl()
    return {
        "value_type": "WAITING_COST",
        "estimated_cost": round(cost, 2),
        "hours_lost": round(wait_hours, 2),
        "confidence_score": 0.7 if wait_hours > 0 else 0.3,
        "inputs": {"wait_hours": wait_hours},
    }


def compute_sla_breach_cost(*, breach_probability: float, impact_brl: float) -> dict[str, Any]:
    prob = min(100, max(0, breach_probability)) / 100
    cost = prob * impact_brl
    return {
        "value_type": "SLA_BREACH_COST",
        "estimated_cost": round(cost, 2),
        "confidence_score": 0.7,
        "inputs": {"breach_probability_pct": breach_probability, "impact_brl": impact_brl},
    }


def compute_operational_costs(
    *,
    card_state: dict[str, Any] | None = None,
    impact_brl: float = 0,
) -> list[dict[str, Any]]:
    """Aggregate all applicable cost types from measurable card/impact data."""
    state = card_state or {}
    costs: list[dict[str, Any]] = []

    days_overdue = state.get("days_overdue", 0) or 0
    if days_overdue > 0:
        costs.append(compute_delay_cost(days_overdue=days_overdue, assignees=state.get("assignee_count", 1)))

    rework = state.get("rework_events", 0) or 0
    if rework > 0:
        costs.append(compute_rework_cost(rework_events=rework))

    blocked_hours = state.get("blocked_hours", 0) or 0
    if blocked_hours > 0:
        costs.append(compute_blocking_cost(blocked_hours=blocked_hours))

    wait_hours = state.get("wait_hours", 0) or 0
    if wait_hours > 0:
        costs.append(compute_waiting_cost(wait_hours=wait_hours))

    sla_prob = state.get("sla_breach_probability", state.get("risk_score", 0)) or 0
    if sla_prob > 0 and impact_brl > 0:
        costs.append(compute_sla_breach_cost(breach_probability=sla_prob, impact_brl=impact_brl))

    return costs
