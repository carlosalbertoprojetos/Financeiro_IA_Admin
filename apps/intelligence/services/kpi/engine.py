"""KPI engine — wraps analytics metrics with extended operational KPIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from django.utils import timezone

from analytics.adapters import load_board_records
from analytics.engine import metrics as metric_engine
from analytics.services.builders import build_cards, build_gaps, build_overview, build_team
from apps.intelligence.services.description_intelligence.summary import aggregate_description_intelligence
from integrations.trello.models import Board, Card


def compute_board_kpis(
    *,
    board_trello_id: str | None = None,
    board_id: int | None = None,
    reference_time: datetime | None = None,
) -> dict[str, Any]:
    """Compute full KPI suite for a board."""
    ref = reference_time or timezone.now()
    cards, actions = load_board_records(
        board_trello_id=board_trello_id,
        board_id=board_id,
        reference_time=ref,
    )

    resolved_board_id = board_trello_id or str(board_id or "")

    overview = build_overview(cards, actions, board_id=resolved_board_id, reference_time=ref)
    team = build_team(cards, actions, board_id=resolved_board_id, reference_time=ref)
    gaps = build_gaps(cards, actions, board_id=resolved_board_id, reference_time=ref)
    card_metrics = build_cards(cards, actions, board_id=resolved_board_id, reference_time=ref)

    lead = metric_engine.lead_time(cards)
    cycle = metric_engine.cycle_time(cards)
    throughput = metric_engine.throughput(cards, reference_time=ref)
    aging = metric_engine.aging(cards, reference_time=ref)
    delay_rate = metric_engine.delay_rate(cards, reference_time=ref)
    rework = metric_engine.rework_rate(actions, cards=cards)

    touch_waiting = _compute_touch_waiting(cards)
    list_dwell = _compute_list_dwell(cards)
    response_time = _compute_avg_response_time(actions)
    sla = _compute_sla_metrics(cards, reference_time=ref)
    description_intelligence = _compute_description_intelligence(board_trello_id=board_trello_id, board_id=board_id)

    return {
        "board_id": board_trello_id or board_id,
        "generated_at": ref.isoformat(),
        "overview": overview,
        "team": team,
        "gaps": gaps,
        "cards": card_metrics,
        "lead_time": lead,
        "cycle_time": cycle,
        "throughput": throughput,
        "aging": aging,
        "delay_rate": delay_rate,
        "rework_rate": rework,
        "touch_time": touch_waiting["touch_time"],
        "waiting_time": touch_waiting["waiting_time"],
        "time_by_list": list_dwell,
        "avg_response_time_hours": response_time,
        "completion_rate": overview.get("completion_rate"),
        "wip": overview.get("wip"),
        "backlog": overview.get("backlog"),
        "sla": sla,
        "description_intelligence": description_intelligence,
        "infrastructure_workload_index": description_intelligence["kpis"].get("infrastructure_workload_index", 0),
        "maintenance_index": description_intelligence["kpis"].get("maintenance_index", 0),
        "incident_density": description_intelligence["kpis"].get("incident_density", 0),
        "correction_rate": description_intelligence["kpis"].get("correction_rate", 0),
        "improvement_rate": description_intelligence["kpis"].get("improvement_rate", 0),
        "preventive_vs_corrective_ratio": description_intelligence["kpis"].get("preventive_vs_corrective_ratio", 0),
        "operational_complexity_score": description_intelligence["kpis"].get("operational_complexity_score", 0),
        "description_completeness": description_intelligence["kpis"].get("description_completeness", 0),
        "operational_documentation_score": description_intelligence["kpis"].get("operational_documentation_score", 0),
        "knowledge_capture_score": description_intelligence["kpis"].get("knowledge_capture_score", 0),
    }


def _compute_touch_waiting(cards: list) -> dict[str, Any]:
    """Estimate touch vs waiting time from status history."""
    touch_hours: list[float] = []
    waiting_hours: list[float] = []

    for card in cards:
        history = list(card.status_history)
        if len(history) < 2:
            continue
        for i in range(len(history) - 1):
            current = history[i]
            next_entry = history[i + 1]
            delta = (next_entry.effective_at - current.effective_at).total_seconds() / 3600
            status_lower = current.status.lower()
            if any(kw in status_lower for kw in ("doing", "progress", "andamento", "dev")):
                touch_hours.append(delta)
            elif any(kw in status_lower for kw in ("wait", "review", "aguardando", "blocked")):
                waiting_hours.append(delta)

    return {
        "touch_time": _summary(touch_hours, "touch_time"),
        "waiting_time": _summary(waiting_hours, "waiting_time"),
    }


def _compute_list_dwell(cards: list) -> dict[str, Any]:
    """Average time spent in each list/status."""
    dwell: dict[str, list[float]] = {}

    for card in cards:
        history = list(card.status_history)
        for i in range(len(history) - 1):
            status = history[i].status or "unknown"
            delta = (history[i + 1].effective_at - history[i].effective_at).total_seconds() / 3600
            dwell.setdefault(status, []).append(delta)

    by_list = {
        status: _summary(values, "hours_in_list")
        for status, values in dwell.items()
    }
    return {"by_list": by_list}


def _compute_avg_response_time(actions: list) -> float | None:
    """Average time between consecutive commentCard actions on same card."""
    from collections import defaultdict

    by_card: dict[str, list] = defaultdict(list)
    for action in actions:
        if action.action_type == "commentCard" and action.card_id:
            by_card[action.card_id].append(action.occurred_at)

    deltas: list[float] = []
    for timestamps in by_card.values():
        sorted_ts = sorted(timestamps)
        for i in range(len(sorted_ts) - 1):
            delta = (sorted_ts[i + 1] - sorted_ts[i]).total_seconds() / 3600
            if delta < 168:
                deltas.append(delta)

    if not deltas:
        return None
    return round(sum(deltas) / len(deltas), 2)


def _compute_sla_metrics(cards: list, *, reference_time: datetime) -> dict[str, Any]:
    with_due = [c for c in cards if c.due_at and not c.is_removed]
    if not with_due:
        return {"total_with_sla": 0, "on_time_pct": None, "breached": 0}

    on_time = 0
    breached = 0
    for card in with_due:
        end = card.completed_at or reference_time
        if card.completed_at and card.due_at and card.completed_at <= card.due_at:
            on_time += 1
        elif not card.completed_at and card.due_at < reference_time:
            breached += 1
        elif card.completed_at and card.due_at and card.completed_at > card.due_at:
            breached += 1
        else:
            on_time += 1

    return {
        "total_with_sla": len(with_due),
        "on_time_pct": round(on_time / len(with_due) * 100, 1) if with_due else None,
        "breached": breached,
    }


def _compute_description_intelligence(
    *,
    board_trello_id: str | None,
    board_id: int | None,
) -> dict[str, Any]:
    board = None
    if board_trello_id:
        board = Board.objects.filter(trello_id=board_trello_id).first()
    elif board_id:
        board = Board.objects.filter(id=board_id).first()
    if not board:
        return {"cards_analyzed": 0, "kpis": {}}

    cards = list(Card.objects.filter(board=board, is_removed=False).select_related("board_list")[:500])
    intelligence = aggregate_description_intelligence(cards)
    kpis = intelligence.get("dashboards", {}).get("executivo", {}).get("kpis", {})
    return {**intelligence, "kpis": kpis}


def _summary(values: list[float], metric: str) -> dict[str, Any]:
    if not values:
        return {"metric": metric, "count": 0, "avg": None, "median": None}
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    median = sorted_vals[n // 2] if n % 2 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
    return {
        "metric": metric,
        "count": n,
        "avg": round(sum(values) / n, 2),
        "median": round(median, 2),
        "unit": "hours",
    }
