from __future__ import annotations

from typing import Any

from analytics.engine import metrics as metric_engine
from apps.intelligence.services.operational_score.scorer import compute_operational_score
from apps.intelligence.services.risk_engine.scorer import assess_card_risk


def generate(
    *,
    cards: list,
    card_records: list,
    actions: list,
    board_id: str,
    filters_meta: dict[str, Any],
) -> dict[str, Any]:
    lead = metric_engine.lead_time(card_records)
    cycle = metric_engine.cycle_time(card_records)
    throughput = metric_engine.throughput(card_records)
    risks = [
        {"card_id": c.trello_id, "title": c.title, **assess_card_risk(c).__dict__}
        for c in cards[:20]
    ]
    score = compute_operational_score(board_trello_id=board_id, persist=False)

    return {
        "report_type": "EXECUTIVO",
        "summary": f"{len(cards)} cards no subconjunto filtrado.",
        "kpis": {
            "lead_time": lead.get("summary"),
            "cycle_time": cycle.get("summary"),
            "throughput": throughput.get("summary"),
        },
        "operational_score": {"score": score.score, "level": score.level},
        "top_risks": sorted(risks, key=lambda r: r["score"], reverse=True)[:5],
        "filters": filters_meta,
    }
