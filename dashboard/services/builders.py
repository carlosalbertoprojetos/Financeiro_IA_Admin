from datetime import datetime, timezone
from typing import Any, Sequence

from analytics.engine.metrics import (
    aging,
    cycle_time,
    delay_rate,
    is_completed,
    lead_time,
    rework_rate,
    throughput,
)
from analytics.engine.types import ActionRecord, CardRecord
from analytics.services.builders import DEFAULT_AGING_GAP_HOURS, UNASSIGNED_KEY, _group_cards_by_assignee, _member_name


def build_dashboard_overview(
    cards: Sequence[CardRecord],
    actions: Sequence[ActionRecord],
    *,
    board_id: str,
    reference_time: datetime | None = None,
    throughput_period: str = "day",
) -> dict[str, Any]:
    now = reference_time or datetime.now(tz=timezone.utc)
    open_cards = [card for card in cards if not is_completed(card)]
    completed_cards = [card for card in cards if is_completed(card)]
    total = len(cards)
    completion_rate = round(len(completed_cards) / total * 100, 2) if total else 0.0

    kpis = {
        "lead_time": lead_time(cards),
        "cycle_time": cycle_time(cards),
        "throughput": throughput(cards, period=throughput_period, reference_time=now),
        "aging": aging(cards, reference_time=now),
        "delay_rate": delay_rate(cards, reference_time=now),
        "rework_rate": rework_rate(actions, cards=cards),
    }

    return {
        "endpoint": "dashboard/overview",
        "board_id": board_id,
        "generated_at": now.isoformat(),
        "summary": {
            "total_cards": total,
            "open_cards": len(open_cards),
            "completed_cards": len(completed_cards),
            "total_actions": len(actions),
            "completion_rate_pct": completion_rate,
        },
        "kpis": {name: _compact_kpi(kpi) for name, kpi in kpis.items()},
        "status_distribution": _status_distribution(cards),
        "health_score": _health_score(kpis),
    }


def build_dashboard_productivity(
    cards: Sequence[CardRecord],
    actions: Sequence[ActionRecord],
    *,
    board_id: str,
    reference_time: datetime | None = None,
    throughput_period: str = "day",
) -> dict[str, Any]:
    now = reference_time or datetime.now(tz=timezone.utc)
    throughput_metric = throughput(cards, period=throughput_period, reference_time=now)
    completed = [card for card in cards if is_completed(card)]
    total = len(cards)

    return {
        "endpoint": "dashboard/productivity",
        "board_id": board_id,
        "generated_at": now.isoformat(),
        "throughput": throughput_metric,
        "completion": {
            "completed_cards": len(completed),
            "open_cards": total - len(completed),
            "completion_rate_pct": round(len(completed) / total * 100, 2) if total else 0.0,
            "average_throughput_per_period": throughput_metric["summary"].get("average_per_period", 0.0),
            "total_completed_in_period": throughput_metric["summary"].get("total_completed", 0),
        },
        "team_output": _team_productivity(cards, actions, reference_time=now),
        "productivity_score": _productivity_score(throughput_metric, len(completed), total),
    }


def build_dashboard_efficiency(
    cards: Sequence[CardRecord],
    actions: Sequence[ActionRecord],
    *,
    board_id: str,
    reference_time: datetime | None = None,
) -> dict[str, Any]:
    now = reference_time or datetime.now(tz=timezone.utc)

    lead = lead_time(cards)
    cycle = cycle_time(cards)
    delay = delay_rate(cards, reference_time=now)
    rework = rework_rate(actions, cards=cards)

    return {
        "endpoint": "dashboard/efficiency",
        "board_id": board_id,
        "generated_at": now.isoformat(),
        "lead_time": lead,
        "cycle_time": cycle,
        "delay_rate": delay,
        "rework_rate": rework,
        "comparison": {
            "lead_time_mean_hours": lead["summary"].get("mean", 0.0),
            "cycle_time_mean_hours": cycle["summary"].get("mean", 0.0),
            "delay_rate_pct": delay["summary"].get("delay_rate_pct", 0.0),
            "rework_rate_pct": rework["summary"].get("rework_rate_pct", 0.0),
        },
        "efficiency_score": _efficiency_score(delay, rework, cycle),
    }


def build_dashboard_bottlenecks(
    cards: Sequence[CardRecord],
    actions: Sequence[ActionRecord],
    *,
    board_id: str,
    reference_time: datetime | None = None,
    aging_threshold_hours: float = DEFAULT_AGING_GAP_HOURS,
) -> dict[str, Any]:
    now = reference_time or datetime.now(tz=timezone.utc)
    aging_metric = aging(cards, reference_time=now)
    delay = delay_rate(cards, reference_time=now)
    rework = rework_rate(actions, cards=cards)

    aging_by_status = _aging_by_status(cards, aging_metric["items"])
    wip_by_status = _wip_by_status(cards)
    threshold = max(aging_threshold_hours, aging_metric["summary"].get("p90") or 0.0)
    top_aging = sorted(
        aging_metric["items"],
        key=lambda item: item["aging_hours"],
        reverse=True,
    )[:10]

    bottleneck_statuses = sorted(
        aging_by_status,
        key=lambda row: row["avg_aging_hours"],
        reverse=True,
    )[:5]

    return {
        "endpoint": "dashboard/bottlenecks",
        "board_id": board_id,
        "generated_at": now.isoformat(),
        "thresholds": {"aging_hours": threshold},
        "summary": {
            "delayed_count": delay["summary"].get("delayed", 0),
            "delay_rate_pct": delay["summary"].get("delay_rate_pct", 0.0),
            "rework_events": rework["summary"].get("rework_events", 0),
            "rework_rate_pct": rework["summary"].get("rework_rate_pct", 0.0),
            "high_aging_count": sum(1 for item in aging_metric["items"] if item["aging_hours"] >= threshold),
            "open_wip": sum(row["count"] for row in wip_by_status),
        },
        "wip_by_status": wip_by_status,
        "aging_by_status": aging_by_status,
        "bottleneck_statuses": bottleneck_statuses,
        "top_aging_cards": top_aging,
        "delayed_cards": delay["items"][:10],
        "rework_events": rework["items"][:10],
    }


def _compact_kpi(kpi: dict[str, Any]) -> dict[str, Any]:
    compact = {
        "metric": kpi.get("metric"),
        "unit": kpi.get("unit"),
        "summary": kpi.get("summary"),
    }
    if "series" in kpi:
        compact["series"] = kpi["series"][:8]
    return compact


def _status_distribution(cards: Sequence[CardRecord]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for card in cards:
        status = card.status or "Sem status"
        counts[status] = counts.get(status, 0) + 1

    return [
        {"status": status, "count": count}
        for status, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)
    ]


def _wip_by_status(cards: Sequence[CardRecord]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for card in cards:
        if is_completed(card):
            continue
        status = card.status or "Sem status"
        counts[status] = counts.get(status, 0) + 1

    return [
        {"status": status, "count": count}
        for status, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)
    ]


def _aging_by_status(
    cards: Sequence[CardRecord],
    aging_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    card_status = {card.id: card.status or "Sem status" for card in cards}
    buckets: dict[str, list[float]] = {}

    for item in aging_items:
        status = card_status.get(item["card_id"], "Sem status")
        buckets.setdefault(status, []).append(float(item["aging_hours"]))

    rows = []
    for status, values in buckets.items():
        rows.append(
            {
                "status": status,
                "count": len(values),
                "avg_aging_hours": round(sum(values) / len(values), 2),
                "max_aging_hours": round(max(values), 2),
            }
        )

    return sorted(rows, key=lambda row: row["avg_aging_hours"], reverse=True)


def _team_productivity(
    cards: Sequence[CardRecord],
    actions: Sequence[ActionRecord],
    *,
    reference_time: datetime,
) -> list[dict[str, Any]]:
    groups = _group_cards_by_assignee(cards)
    rows: list[dict[str, Any]] = []

    for member_id, member_cards in sorted(groups.items(), key=lambda item: item[0]):
        if member_id == UNASSIGNED_KEY:
            continue

        completed = [card for card in member_cards if is_completed(card)]
        card_ids = {card.id for card in member_cards}
        member_actions = [action for action in actions if action.card_id in card_ids]
        throughput_metric = throughput(member_cards, reference_time=reference_time)

        rows.append(
            {
                "member_id": member_id,
                "member_name": _member_name(member_id, member_cards),
                "card_count": len(member_cards),
                "completed_cards": len(completed),
                "completion_rate_pct": round(len(completed) / len(member_cards) * 100, 2)
                if member_cards
                else 0.0,
                "throughput_total": throughput_metric["summary"].get("total_completed", 0),
                "delay_rate_pct": delay_rate(member_cards, reference_time=reference_time)["summary"].get(
                    "delay_rate_pct", 0.0
                ),
                "rework_rate_pct": rework_rate(member_actions, cards=member_cards)["summary"].get(
                    "rework_rate_pct", 0.0
                ),
            }
        )

    return rows


def _health_score(kpis: dict[str, dict[str, Any]]) -> float:
    delay = float(kpis["delay_rate"]["summary"].get("delay_rate_pct", 0.0))
    rework = float(kpis["rework_rate"]["summary"].get("rework_rate_pct", 0.0))
    aging_mean = float(kpis["aging"]["summary"].get("mean", 0.0))
    aging_penalty = min(aging_mean / 24.0 * 5.0, 25.0)
    return round(max(0.0, 100.0 - delay - rework * 0.5 - aging_penalty), 1)


def _productivity_score(throughput_metric: dict[str, Any], completed: int, total: int) -> float:
    avg = float(throughput_metric["summary"].get("average_per_period", 0.0))
    completion_rate = (completed / total * 100) if total else 0.0
    throughput_component = min(avg * 10.0, 50.0)
    completion_component = completion_rate * 0.5
    return round(min(100.0, throughput_component + completion_component), 1)


def _efficiency_score(
    delay: dict[str, Any],
    rework: dict[str, Any],
    cycle: dict[str, Any],
) -> float:
    delay_pct = float(delay["summary"].get("delay_rate_pct", 0.0))
    rework_pct = float(rework["summary"].get("rework_rate_pct", 0.0))
    cycle_mean = float(cycle["summary"].get("mean", 0.0))
    cycle_penalty = min(cycle_mean / 48.0 * 10.0, 20.0)
    return round(max(0.0, 100.0 - delay_pct - rework_pct * 0.5 - cycle_penalty), 1)
