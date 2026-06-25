from __future__ import annotations

from collections import defaultdict
from typing import Any

from analytics.engine import metrics as metric_engine
from apps.intelligence.services.operational_score.scorer import compute_operational_score
from apps.intelligence.services.report_query.domain.title_parser import extract_prefix, parse_structured_title
from apps.intelligence.services.risk_engine.scorer import assess_card_risk
from apps.intelligence.services.timeline.engine import build_card_timeline


def generate(
    *,
    cards: list,
    card_records: list,
    actions: list,
    board_id: str,
    filters_meta: dict[str, Any],
) -> dict[str, Any]:
    prefix_filter = filters_meta.get("filters_applied", {}).get("title_prefix", "")
    by_prefix: dict[str, list] = defaultdict(list)

    for card in cards:
        parsed = parse_structured_title(card.title)
        category = parsed["category"] or "SEM_PREFIXO"
        if prefix_filter and category != prefix_filter.upper():
            continue
        by_prefix[category].append(card)

    prefixes_report = []
    for prefix, prefix_cards in by_prefix.items():
        ids = {c.trello_id for c in prefix_cards}
        scoped = [cr for cr in card_records if cr.id in ids]
        lead = metric_engine.lead_time(scoped)
        cycle = metric_engine.cycle_time(scoped)
        risks = sorted(
            [{"card_id": c.trello_id, "score": assess_card_risk(c).score} for c in prefix_cards],
            key=lambda x: x["score"],
            reverse=True,
        )[:5]

        prefixes_report.append(
            {
                "prefix": prefix,
                "card_count": len(prefix_cards),
                "executive_summary": f"{len(prefix_cards)} cards na categoria [{prefix}]",
                "kpis": {
                    "lead_time": lead.get("summary"),
                    "cycle_time": cycle.get("summary"),
                },
                "timeline_sample": build_card_timeline(prefix_cards[0])[:10] if prefix_cards else [],
                "top_risks": risks,
                "recommendations": [
                    f"Revisar carga da categoria [{prefix}]"
                    if len(prefix_cards) > 5
                    else f"Categoria [{prefix}] sob controle"
                ],
            }
        )

    score = compute_operational_score(board_trello_id=board_id, persist=False)

    return {
        "report_type": "PREFIXO",
        "prefixes": prefixes_report,
        "operational_score": {"score": score.score, "level": score.level},
        "filters": filters_meta,
    }
