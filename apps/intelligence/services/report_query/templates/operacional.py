from __future__ import annotations

from typing import Any

from analytics.engine import metrics as metric_engine


def generate(
    *,
    cards: list,
    card_records: list,
    actions: list,
    board_id: str,
    filters_meta: dict[str, Any],
) -> dict[str, Any]:
    aging = metric_engine.aging(card_records)
    rework = metric_engine.rework_rate(actions, cards=card_records)

    return {
        "report_type": "OPERACIONAL",
        "card_count": len(cards),
        "wip": sum(1 for c in cards if not c.is_closed),
        "aging": aging.get("summary"),
        "rework_rate": rework.get("summary"),
        "cards": [
            {"id": c.trello_id, "title": c.title, "status": c.status}
            for c in cards[:50]
        ],
        "filters": filters_meta,
    }
