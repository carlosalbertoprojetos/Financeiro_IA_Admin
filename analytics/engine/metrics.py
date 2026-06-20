from datetime import datetime, timezone
from statistics import mean, median
from typing import Any, Iterable, Sequence

from analytics.engine.types import ActionRecord, CardRecord

DEFAULT_DONE_STATUSES = frozenset(
    {"done", "concluído", "concluido", "closed", "complete", "completed", "finalizado"}
)
REWORK_ACTION_TYPES = frozenset({"updateCard"})


def lead_time(cards: Sequence[CardRecord]) -> dict[str, Any]:
    """Time from card creation to completion (hours)."""
    items: list[dict[str, Any]] = []

    for card in cards:
        end = _completion_time(card)
        if not card.created_at or not end:
            continue

        duration_hours = _hours_between(card.created_at, end)
        items.append(
            {
                "card_id": card.id,
                "title": card.title,
                "lead_time_hours": duration_hours,
                "started_at": card.created_at.isoformat(),
                "completed_at": end.isoformat(),
            }
        )

    values = [item["lead_time_hours"] for item in items]
    return {
        "metric": "lead_time",
        "unit": "hours",
        "summary": _numeric_summary(values),
        "items": items,
    }


def cycle_time(
    cards: Sequence[CardRecord],
    *,
    start_statuses: frozenset[str] | None = None,
    done_statuses: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Time from first active work to completion (hours)."""
    done = done_statuses or DEFAULT_DONE_STATUSES
    items: list[dict[str, Any]] = []

    for card in cards:
        end = _completion_time(card, done_statuses=done)
        start = _cycle_start(card, start_statuses=start_statuses)
        if not start or not end or end <= start:
            continue

        duration_hours = _hours_between(start, end)
        items.append(
            {
                "card_id": card.id,
                "title": card.title,
                "cycle_time_hours": duration_hours,
                "started_at": start.isoformat(),
                "completed_at": end.isoformat(),
            }
        )

    values = [item["cycle_time_hours"] for item in items]
    return {
        "metric": "cycle_time",
        "unit": "hours",
        "summary": _numeric_summary(values),
        "items": items,
    }


def throughput(
    cards: Sequence[CardRecord],
    *,
    period: str = "day",
    reference_time: datetime | None = None,
) -> dict[str, Any]:
    """Completed cards grouped by day or week."""
    if period not in {"day", "week"}:
        raise ValueError("period must be 'day' or 'week'")

    buckets: dict[str, int] = {}
    items: list[dict[str, Any]] = []

    for card in cards:
        completed = _completion_time(card)
        if not completed:
            continue

        bucket_key = _period_key(completed, period)
        buckets[bucket_key] = buckets.get(bucket_key, 0) + 1
        items.append(
            {
                "card_id": card.id,
                "title": card.title,
                "completed_at": completed.isoformat(),
                "period": bucket_key,
            }
        )

    series = [{"period": key, "count": count} for key, count in sorted(buckets.items())]
    completion_times = [_completion_time(card) for card in cards]
    has_completions = any(completion_times)

    return {
        "metric": "throughput",
        "unit": "cards",
        "period": period,
        "reference_time": _ensure_aware_iso(reference_time or _max_datetime(completion_times))
        if has_completions
        else None,
        "summary": {
            "total_completed": len(items),
            "periods": len(series),
            "average_per_period": round(mean([row["count"] for row in series]), 2) if series else 0.0,
        },
        "series": series,
        "items": items,
    }


def aging(
    cards: Sequence[CardRecord],
    *,
    reference_time: datetime | None = None,
) -> dict[str, Any]:
    """Age of open cards in their current status (hours)."""
    now = reference_time or datetime.now(tz=timezone.utc)
    items: list[dict[str, Any]] = []

    for card in cards:
        if _is_completed(card):
            continue

        status_entered_at = _current_status_entered_at(card)
        if not status_entered_at:
            continue

        age_hours = _hours_between(status_entered_at, now)
        items.append(
            {
                "card_id": card.id,
                "title": card.title,
                "status": card.status,
                "aging_hours": age_hours,
                "status_entered_at": status_entered_at.isoformat(),
            }
        )

    values = [item["aging_hours"] for item in items]
    return {
        "metric": "aging",
        "unit": "hours",
        "reference_time": _ensure_aware_iso(now),
        "summary": _numeric_summary(values),
        "items": items,
    }


def delay_rate(
    cards: Sequence[CardRecord],
    *,
    reference_time: datetime | None = None,
) -> dict[str, Any]:
    """Share of cards that missed their due date."""
    now = reference_time or datetime.now(tz=timezone.utc)
    eligible = [card for card in cards if card.due_at is not None]
    delayed_items: list[dict[str, Any]] = []

    for card in eligible:
        completed = _completion_time(card)
        is_delayed = False
        delay_hours = 0.0

        if completed and card.due_at and completed > card.due_at:
            is_delayed = True
            delay_hours = _hours_between(card.due_at, completed)
        elif not completed and card.due_at and now > card.due_at:
            is_delayed = True
            delay_hours = _hours_between(card.due_at, now)

        if is_delayed:
            delayed_items.append(
                {
                    "card_id": card.id,
                    "title": card.title,
                    "due_at": card.due_at.isoformat(),
                    "completed_at": completed.isoformat() if completed else None,
                    "delay_hours": delay_hours,
                    "status": card.status,
                }
            )

    total = len(eligible)
    delayed = len(delayed_items)
    rate = round(delayed / total, 4) if total else 0.0

    return {
        "metric": "delay_rate",
        "unit": "ratio",
        "reference_time": _ensure_aware_iso(now),
        "summary": {
            "total_with_due_date": total,
            "delayed": delayed,
            "on_time": total - delayed,
            "delay_rate": rate,
            "delay_rate_pct": round(rate * 100, 2),
        },
        "items": delayed_items,
    }


def rework_rate(
    actions: Sequence[ActionRecord],
    *,
    cards: Sequence[CardRecord] | None = None,
) -> dict[str, Any]:
    """
    Share of cards with backward workflow moves (rework).

    Detects updateCard actions where the card moves to an earlier list position.
    """
    card_titles = {card.id: card.title for card in cards} if cards else {}
    rework_events: list[dict[str, Any]] = []
    cards_with_rework: set[str] = set()

    for action in actions:
        if action.action_type not in REWORK_ACTION_TYPES:
            continue

        card_id = action.card_id or _extract_card_id(action.raw_json)
        if not card_id:
            continue

        list_before = _extract_list(action.raw_json, "listBefore")
        list_after = _extract_list(action.raw_json, "listAfter")
        if not list_before or not list_after:
            continue

        before_pos = list_before.get("pos")
        after_pos = list_after.get("pos")
        if before_pos is None or after_pos is None:
            continue

        if after_pos < before_pos:
            cards_with_rework.add(card_id)
            rework_events.append(
                {
                    "action_id": action.id,
                    "card_id": card_id,
                    "title": card_titles.get(card_id, ""),
                    "occurred_at": action.occurred_at.isoformat(),
                    "from_list": list_before.get("name"),
                    "to_list": list_after.get("name"),
                    "from_position": before_pos,
                    "to_position": after_pos,
                }
            )

    denominator = len(cards) if cards else _unique_card_ids_from_actions(actions)
    rate = round(len(cards_with_rework) / denominator, 4) if denominator else 0.0

    return {
        "metric": "rework_rate",
        "unit": "ratio",
        "summary": {
            "cards_with_rework": len(cards_with_rework),
            "rework_events": len(rework_events),
            "cards_considered": denominator,
            "rework_rate": rate,
            "rework_rate_pct": round(rate * 100, 2),
        },
        "items": rework_events,
    }


def compute_all(
    cards: Sequence[CardRecord],
    actions: Sequence[ActionRecord],
    *,
    reference_time: datetime | None = None,
    throughput_period: str = "day",
) -> dict[str, Any]:
    """Run all analytics metrics and return structured JSON."""
    now = reference_time or datetime.now(tz=timezone.utc)
    return {
        "generated_at": _ensure_aware_iso(now),
        "input": {
            "cards": len(cards),
            "actions": len(actions),
        },
        "metrics": {
            "lead_time": lead_time(cards),
            "cycle_time": cycle_time(cards),
            "throughput": throughput(cards, period=throughput_period, reference_time=now),
            "aging": aging(cards, reference_time=now),
            "delay_rate": delay_rate(cards, reference_time=now),
            "rework_rate": rework_rate(actions, cards=cards),
        },
    }


def _numeric_summary(values: list[float]) -> dict[str, Any]:
    if not values:
        return {
            "count": 0,
            "mean": 0.0,
            "median": 0.0,
            "p90": 0.0,
            "min": 0.0,
            "max": 0.0,
        }

    ordered = sorted(values)
    p90_index = max(int(len(ordered) * 0.9) - 1, 0)

    return {
        "count": len(values),
        "mean": round(mean(values), 2),
        "median": round(median(values), 2),
        "p90": round(ordered[p90_index], 2),
        "min": round(ordered[0], 2),
        "max": round(ordered[-1], 2),
    }


def _completion_time(
    card: CardRecord,
    *,
    done_statuses: frozenset[str] | None = None,
) -> datetime | None:
    done = done_statuses or DEFAULT_DONE_STATUSES

    if card.completed_at:
        return card.completed_at

    if card.is_closed:
        return _last_history_time(card) or card.created_at

    if card.status.casefold() in done:
        return _last_history_time(card) or card.created_at

    return None


def _cycle_start(
    card: CardRecord,
    *,
    start_statuses: frozenset[str] | None = None,
) -> datetime | None:
    if start_statuses:
        normalized = {status.casefold() for status in start_statuses}
        for transition in card.status_history:
            if transition.status.casefold() in normalized:
                return transition.effective_at
        return None

    if card.status_history:
        if len(card.status_history) >= 2:
            return card.status_history[1].effective_at
        return card.status_history[0].effective_at

    return card.created_at


def _current_status_entered_at(card: CardRecord) -> datetime | None:
    if card.status_history:
        return card.status_history[-1].effective_at
    return card.created_at


def is_completed(card: CardRecord) -> bool:
    """Return True when the card is considered done."""
    return _completion_time(card) is not None


def _is_completed(card: CardRecord) -> bool:
    return is_completed(card)


def _hours_between(start: datetime, end: datetime) -> float:
    start_aware = _ensure_aware(start)
    end_aware = _ensure_aware(end)
    return round((end_aware - start_aware).total_seconds() / 3600, 2)


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _ensure_aware_iso(value: datetime) -> str:
    return _ensure_aware(value).isoformat()


def _period_key(value: datetime, period: str) -> str:
    if period == "week":
        year, week, _ = value.isocalendar()
        return f"{year}-W{week:02d}"
    return _ensure_aware(value).date().isoformat()


def _max_datetime(values: Iterable[datetime | None]) -> datetime:
    filtered = [value for value in values if value is not None]
    return max(filtered) if filtered else datetime.now(tz=timezone.utc)


def _last_history_time(card: CardRecord) -> datetime | None:
    if not card.status_history:
        return None
    return card.status_history[-1].effective_at


def _extract_card_id(raw_json: dict[str, Any]) -> str | None:
    data = raw_json.get("data") or {}
    card = data.get("card") or {}
    return card.get("id")


def _extract_list(raw_json: dict[str, Any], key: str) -> dict[str, Any] | None:
    data = raw_json.get("data") or {}
    value = data.get(key)
    return value if isinstance(value, dict) else None


def _unique_card_ids_from_actions(actions: Sequence[ActionRecord]) -> int:
    card_ids = {
        action.card_id or _extract_card_id(action.raw_json)
        for action in actions
        if action.card_id or _extract_card_id(action.raw_json)
    }
    return len(card_ids)
