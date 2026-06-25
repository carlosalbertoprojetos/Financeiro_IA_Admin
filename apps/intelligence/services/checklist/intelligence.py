"""Checklist intelligence — execution metrics and scoring."""

from __future__ import annotations

from typing import Any

from apps.intelligence.domain.entities import ChecklistMetrics
from integrations.trello.models import Card


def analyze_checklists(card: Card) -> ChecklistMetrics:
    """Compute checklist completion metrics from card raw_json."""
    checklists = _extract_checklists(card)
    if not checklists:
        return ChecklistMetrics(card_id=card.trello_id, execution_score=100.0)

    total = 0
    completed = 0
    critical_pending: list[str] = []
    blocked: list[str] = []
    overdue: list[str] = []
    never_started: list[str] = []

    for checklist in checklists:
        checklist_name = checklist.get("name") or "Checklist"
        items = checklist.get("checkItems") or []
        for item in items:
            total += 1
            name = item.get("name") or "Item"
            state = item.get("state") or "incomplete"
            full_name = f"{checklist_name}: {name}"

            if state == "complete":
                completed += 1
            else:
                if _is_critical(name):
                    critical_pending.append(full_name)
                if _is_blocked(name):
                    blocked.append(full_name)
                if _is_overdue_item(item):
                    overdue.append(full_name)
                if not item.get("idMember"):
                    never_started.append(full_name)

    pending = total - completed
    completion_pct = round((completed / total) * 100, 1) if total else 100.0
    execution_score = _compute_execution_score(
        completion_pct,
        len(critical_pending),
        len(blocked),
        len(overdue),
        len(never_started),
    )

    return ChecklistMetrics(
        card_id=card.trello_id,
        total_items=total,
        completed_items=completed,
        pending_items=pending,
        completion_pct=completion_pct,
        critical_pending=tuple(critical_pending),
        blocked_items=tuple(blocked),
        overdue_items=tuple(overdue),
        never_started=tuple(never_started),
        execution_score=execution_score,
    )


def _extract_checklists(card: Card) -> list[dict[str, Any]]:
    raw = card.raw_json or {}
    checklists = raw.get("checklists") or raw.get("idChecklists")
    if isinstance(checklists, list) and checklists and isinstance(checklists[0], dict):
        return checklists
    if isinstance(checklists, list):
        return [{"name": "Checklist", "checkItems": []} for _ in checklists]
    badges = raw.get("badges") or {}
    if badges.get("checkItems") or badges.get("checkItemsCheck"):
        return [
            {
                "name": "Checklist",
                "checkItems": _synthetic_items_from_badges(badges),
            }
        ]
    return []


def _synthetic_items_from_badges(badges: dict[str, Any]) -> list[dict[str, Any]]:
    total = int(badges.get("checkItems") or 0)
    done = int(badges.get("checkItemsCheck") or 0)
    items: list[dict[str, Any]] = []
    for i in range(total):
        items.append(
            {
                "name": f"Item {i + 1}",
                "state": "complete" if i < done else "incomplete",
            }
        )
    return items


def _is_critical(name: str) -> bool:
    lower = name.lower()
    return any(kw in lower for kw in ("crítico", "critico", "critical", "obrigatório", "obrigatorio"))


def _is_blocked(name: str) -> bool:
    lower = name.lower()
    return any(kw in lower for kw in ("bloqueio", "blocker", "blocked", "impedimento"))


def _is_overdue_item(item: dict[str, Any]) -> bool:
    due = item.get("due")
    if not due:
        return False
    from django.utils.dateparse import parse_datetime

    parsed = parse_datetime(str(due))
    if not parsed:
        return False
    from django.utils import timezone

    return parsed < timezone.now() and item.get("state") != "complete"


def _compute_execution_score(
    completion_pct: float,
    critical_pending: int,
    blocked: int,
    overdue: int,
    never_started: int,
) -> float:
    score = completion_pct
    score -= critical_pending * 10
    score -= blocked * 15
    score -= overdue * 8
    score -= never_started * 3
    return round(max(0.0, min(100.0, score)), 1)
