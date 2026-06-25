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
    throughput = metric_engine.throughput(card_records)
    rework = metric_engine.rework_rate(actions, cards=card_records)
    completed = sum(1 for c in cards if c.is_closed)

    return {
        "report_type": "PRODUTIVIDADE",
        "completed_count": completed,
        "total_count": len(cards),
        "completion_rate": round(completed / len(cards) * 100, 1) if cards else 0,
        "throughput": throughput.get("summary"),
        "rework_rate": rework.get("summary"),
        "filters": filters_meta,
    }
