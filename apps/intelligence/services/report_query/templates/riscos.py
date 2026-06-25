from __future__ import annotations

from typing import Any

from apps.intelligence.services.risk_engine.scorer import assess_card_risk


def generate(
    *,
    cards: list,
    card_records: list,
    actions: list,
    board_id: str,
    filters_meta: dict[str, Any],
) -> dict[str, Any]:
    assessments = []
    for card in cards:
        risk = assess_card_risk(card)
        assessments.append(
            {
                "card_id": card.trello_id,
                "title": card.title,
                "score": risk.score,
                "level": risk.level,
                "factors": list(risk.factors),
            }
        )

    by_level: dict[str, int] = {}
    for item in assessments:
        by_level[item["level"]] = by_level.get(item["level"], 0) + 1

    return {
        "report_type": "RISCOS",
        "total_assessed": len(assessments),
        "by_level": by_level,
        "assessments": sorted(assessments, key=lambda x: x["score"], reverse=True),
        "filters": filters_meta,
    }
