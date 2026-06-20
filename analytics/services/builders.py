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

DEFAULT_AGING_GAP_HOURS = 72.0
UNASSIGNED_KEY = "__unassigned__"


def build_overview(
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

    return {
        "endpoint": "metrics/overview",
        "board_id": board_id,
        "generated_at": now.isoformat(),
        "counts": {
            "total_cards": len(cards),
            "open_cards": len(open_cards),
            "completed_cards": len(completed_cards),
            "total_actions": len(actions),
        },
        "kpis": {
            "lead_time": lead_time(cards),
            "cycle_time": cycle_time(cards),
            "throughput": throughput(cards, period=throughput_period, reference_time=now),
            "aging": aging(cards, reference_time=now),
            "delay_rate": delay_rate(cards, reference_time=now),
            "rework_rate": rework_rate(actions, cards=cards),
        },
    }


def build_team(
    cards: Sequence[CardRecord],
    actions: Sequence[ActionRecord],
    *,
    board_id: str,
    reference_time: datetime | None = None,
) -> dict[str, Any]:
    now = reference_time or datetime.now(tz=timezone.utc)
    groups = _group_cards_by_assignee(cards)
    members: list[dict[str, Any]] = []

    for member_id, member_cards in sorted(groups.items(), key=lambda item: item[0]):
        if member_id == UNASSIGNED_KEY:
            continue

        member_name = _member_name(member_id, member_cards)
        card_ids = {card.id for card in member_cards}
        member_actions = [action for action in actions if action.card_id in card_ids]

        members.append(
            {
                "member_id": member_id,
                "member_name": member_name,
                "card_count": len(member_cards),
                "metrics": _team_metrics(member_cards, member_actions, reference_time=now),
            }
        )

    unassigned_cards = groups.get(UNASSIGNED_KEY, [])
    unassigned_ids = {card.id for card in unassigned_cards}
    unassigned_actions = [action for action in actions if action.card_id in unassigned_ids]

    return {
        "endpoint": "metrics/team",
        "board_id": board_id,
        "generated_at": now.isoformat(),
        "members": members,
        "unassigned": {
            "card_count": len(unassigned_cards),
            "metrics": _team_metrics(unassigned_cards, unassigned_actions, reference_time=now),
        },
    }


def build_cards(
    cards: Sequence[CardRecord],
    actions: Sequence[ActionRecord],
    *,
    board_id: str,
    reference_time: datetime | None = None,
) -> dict[str, Any]:
    now = reference_time or datetime.now(tz=timezone.utc)

    lead_by_id = {item["card_id"]: item for item in lead_time(cards)["items"]}
    cycle_by_id = {item["card_id"]: item for item in cycle_time(cards)["items"]}
    aging_by_id = {item["card_id"]: item for item in aging(cards, reference_time=now)["items"]}
    delayed_ids = {item["card_id"] for item in delay_rate(cards, reference_time=now)["items"]}
    rework_by_id = _rework_cards_map(actions)

    card_rows: list[dict[str, Any]] = []
    for card in cards:
        card_rows.append(
            {
                "card_id": card.id,
                "title": card.title,
                "status": card.status,
                "is_closed": card.is_closed,
                "is_removed": card.is_removed,
                "assignees": [
                    {"id": assignee_id, "name": name}
                    for assignee_id, name in zip(card.assignee_ids, card.assignee_names)
                ],
                "labels": list(card.labels),
                "priority": _infer_priority(card.labels),
                "due_at": card.due_at.isoformat() if card.due_at else None,
                "lead_time_hours": lead_by_id.get(card.id, {}).get("lead_time_hours"),
                "cycle_time_hours": cycle_by_id.get(card.id, {}).get("cycle_time_hours"),
                "aging_hours": aging_by_id.get(card.id, {}).get("aging_hours"),
                "is_delayed": card.id in delayed_ids,
                "has_rework": card.id in rework_by_id,
                "rework_events": rework_by_id.get(card.id, 0),
            }
        )

    return {
        "endpoint": "metrics/cards",
        "board_id": board_id,
        "generated_at": now.isoformat(),
        "summary": {
            "total_cards": len(card_rows),
            "delayed": sum(1 for row in card_rows if row["is_delayed"]),
            "with_rework": sum(1 for row in card_rows if row["has_rework"]),
        },
        "cards": card_rows,
    }


def build_gaps(
    cards: Sequence[CardRecord],
    actions: Sequence[ActionRecord],
    *,
    board_id: str,
    reference_time: datetime | None = None,
    aging_threshold_hours: float = DEFAULT_AGING_GAP_HOURS,
) -> dict[str, Any]:
    now = reference_time or datetime.now(tz=timezone.utc)

    delayed = delay_rate(cards, reference_time=now)
    aging_metric = aging(cards, reference_time=now)
    rework = rework_rate(actions, cards=cards)

    aging_threshold = max(aging_threshold_hours, aging_metric["summary"].get("p90") or 0.0)
    aging_high = [
        item for item in aging_metric["items"] if item["aging_hours"] >= aging_threshold
    ]
    unassigned_open = [
        {
            "card_id": card.id,
            "title": card.title,
            "status": card.status,
            "gap_type": "unassigned",
        }
        for card in cards
        if not card.assignee_ids and not is_completed(card)
    ]

    gaps = {
        "delayed": delayed["items"],
        "aging_high": aging_high,
        "rework": rework["items"],
        "unassigned_open": unassigned_open,
    }

    total_gaps = (
        len(gaps["delayed"])
        + len(gaps["aging_high"])
        + len(gaps["rework"])
        + len(gaps["unassigned_open"])
    )

    return {
        "endpoint": "metrics/gaps",
        "board_id": board_id,
        "generated_at": now.isoformat(),
        "thresholds": {
            "aging_hours": aging_threshold,
        },
        "summary": {
            "total_gaps": total_gaps,
            "delayed_count": len(gaps["delayed"]),
            "aging_high_count": len(gaps["aging_high"]),
            "rework_count": len(gaps["rework"]),
            "unassigned_open_count": len(gaps["unassigned_open"]),
            "delay_rate_pct": delayed["summary"].get("delay_rate_pct", 0.0),
            "rework_rate_pct": rework["summary"].get("rework_rate_pct", 0.0),
        },
        "gaps": gaps,
    }


def _team_metrics(
    cards: Sequence[CardRecord],
    actions: Sequence[ActionRecord],
    *,
    reference_time: datetime,
) -> dict[str, Any]:
    return {
        "lead_time": lead_time(cards),
        "cycle_time": cycle_time(cards),
        "aging": aging(cards, reference_time=reference_time),
        "delay_rate": delay_rate(cards, reference_time=reference_time),
        "rework_rate": rework_rate(actions, cards=cards),
    }


def _group_cards_by_assignee(cards: Sequence[CardRecord]) -> dict[str, list[CardRecord]]:
    groups: dict[str, list[CardRecord]] = {}

    for card in cards:
        if not card.assignee_ids:
            groups.setdefault(UNASSIGNED_KEY, []).append(card)
            continue

        for assignee_id in card.assignee_ids:
            groups.setdefault(assignee_id, []).append(card)

    return groups


def _member_name(member_id: str, cards: Sequence[CardRecord]) -> str:
    for card in cards:
        for index, assignee_id in enumerate(card.assignee_ids):
            if assignee_id == member_id:
                if index < len(card.assignee_names):
                    return card.assignee_names[index]
                return assignee_id
    return member_id


def _rework_cards_map(actions: Sequence[ActionRecord]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in rework_rate(actions)["items"]:
        card_id = item["card_id"]
        counts[card_id] = counts.get(card_id, 0) + 1
    return counts


def _infer_priority(labels: tuple[dict[str, str], ...] | list[dict[str, str]]) -> str:
    if not labels:
        return "none"

    high_colors = {"red", "orange", "pink"}
    medium_colors = {"yellow", "purple", "sky"}
    low_colors = {"green", "blue", "lime", "black"}

    for label in labels:
        name = (label.get("name") or "").casefold()
        color = (label.get("color") or "").casefold()

        if any(token in name for token in ("alta", "high", "urgent", "urgente", "critical")):
            return "high"
        if any(token in name for token in ("media", "medium", "normal")):
            return "medium"
        if any(token in name for token in ("baixa", "low")):
            return "low"
        if color in high_colors:
            return "high"
        if color in medium_colors:
            return "medium"
        if color in low_colors:
            return "low"

    return "none"