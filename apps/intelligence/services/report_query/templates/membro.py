from __future__ import annotations

from collections import defaultdict
from typing import Any

from django.utils import timezone

from analytics.engine import metrics as metric_engine
from apps.intelligence.services.risk_engine.scorer import assess_card_risk


def generate(
    *,
    cards: list,
    card_records: list,
    actions: list,
    board_id: str,
    filters_meta: dict[str, Any],
) -> dict[str, Any]:
    now = timezone.now()
    by_member: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "open_cards": 0,
            "completed": 0,
            "overdue": 0,
            "risk_scores": [],
            "card_ids": [],
        }
    )

    for card in cards:
        assignees = list(card.assignees.all()) or [None]
        for member in assignees:
            key = member.full_name if member else "Não atribuído"
            stats = by_member[key]
            stats["card_ids"].append(card.trello_id)
            if card.is_closed:
                stats["completed"] += 1
            else:
                stats["open_cards"] += 1
            if card.due_at and card.due_at < now and not card.is_closed:
                stats["overdue"] += 1
            stats["risk_scores"].append(assess_card_risk(card).score)

    members_report = []
    for name, stats in by_member.items():
        total = stats["open_cards"] + stats["completed"]
        avg_risk = sum(stats["risk_scores"]) / len(stats["risk_scores"]) if stats["risk_scores"] else 0
        member_cards = [c for c in card_records if c.id in stats["card_ids"]]
        lead = metric_engine.lead_time(member_cards)

        members_report.append(
            {
                "member": name,
                "volume": total,
                "completed": stats["completed"],
                "overdue": stats["overdue"],
                "open_load": stats["open_cards"],
                "avg_lead_time_hours": lead.get("summary", {}).get("avg"),
                "completion_rate": round(stats["completed"] / total * 100, 1) if total else 0,
                "avg_risk_score": round(avg_risk, 1),
                "individual_score": max(0, int(100 - avg_risk)),
                "trend": "stable",
            }
        )

    return {
        "report_type": "MEMBRO",
        "members": sorted(members_report, key=lambda m: m["volume"], reverse=True),
        "filters": filters_meta,
    }
