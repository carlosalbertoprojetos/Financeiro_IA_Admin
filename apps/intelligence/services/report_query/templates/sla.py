from __future__ import annotations

from typing import Any

from django.utils import timezone


def generate(
    *,
    cards: list,
    card_records: list,
    actions: list,
    board_id: str,
    filters_meta: dict[str, Any],
) -> dict[str, Any]:
    now = timezone.now()
    with_due = [c for c in cards if c.due_at]
    on_time = 0
    breached = 0
    at_risk = 0

    for card in with_due:
        if card.completed_at and card.due_at:
            if card.completed_at <= card.due_at:
                on_time += 1
            else:
                breached += 1
        elif not card.completed_at and card.due_at < now:
            breached += 1
        elif not card.completed_at and card.due_at and (card.due_at - now).days <= 2:
            at_risk += 1
        else:
            on_time += 1

    total = len(with_due)
    return {
        "report_type": "SLA",
        "total_with_sla": total,
        "on_time": on_time,
        "breached": breached,
        "at_risk": at_risk,
        "compliance_pct": round(on_time / total * 100, 1) if total else None,
        "filters": filters_meta,
    }
