from __future__ import annotations

from collections import defaultdict
from typing import Any

from analytics.engine import metrics as metric_engine
from apps.intelligence.services.report_query.engine.card_metrics import get_card_label_names
from apps.intelligence.services.risk_engine.scorer import assess_card_risk


def generate(
    *,
    cards: list,
    card_records: list,
    actions: list,
    board_id: str,
    filters_meta: dict[str, Any],
) -> dict[str, Any]:
    by_label: dict[str, list] = defaultdict(list)
    for card in cards:
        labels = get_card_label_names(card) or ["Sem etiqueta"]
        for label in labels:
            by_label[label].append(card)

    labels_report = []
    for label, label_cards in by_label.items():
        ids = {c.trello_id for c in label_cards}
        scoped_records = [cr for cr in card_records if cr.id in ids]
        lead = metric_engine.lead_time(scoped_records)
        cycle = metric_engine.cycle_time(scoped_records)
        risks = [assess_card_risk(c).score for c in label_cards]

        assignee_counts: dict[str, int] = defaultdict(int)
        for card in label_cards:
            for member in card.assignees.all():
                assignee_counts[member.full_name or member.username] += 1

        labels_report.append(
            {
                "label": label,
                "card_count": len(label_cards),
                "lead_time_avg": lead.get("summary", {}).get("avg"),
                "cycle_time_avg": cycle.get("summary", {}).get("avg"),
                "avg_risk": round(sum(risks) / len(risks), 1) if risks else 0,
                "top_assignees": sorted(assignee_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                "bottleneck_hint": label if len(label_cards) > 10 else None,
            }
        )

    return {
        "report_type": "ETIQUETA",
        "labels": sorted(labels_report, key=lambda x: x["card_count"], reverse=True),
        "filters": filters_meta,
    }
