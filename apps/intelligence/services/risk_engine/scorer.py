"""Risk engine — operational risk scoring 0-100."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from django.utils import timezone

from analytics.adapters import load_board_records
from apps.intelligence.domain.entities import RiskAssessment
from apps.intelligence.services.checklist.intelligence import analyze_checklists
from apps.intelligence.services.communication_analysis.analyzer import analyze_communication
from integrations.trello.models import Card


RISK_LEVELS = [
    (75, "Crítico"),
    (50, "Alto"),
    (25, "Moderado"),
    (0, "Baixo"),
]


def assess_card_risk(card: Card, *, reference_time: datetime | None = None) -> RiskAssessment:
    """Compute operational risk score for a single card."""
    ref = reference_time or timezone.now()
    factors: list[dict[str, Any]] = []
    score = 0

    if card.due_at and not card.completed_at and card.due_at < ref:
        days_overdue = (ref - card.due_at).days
        points = min(30, 10 + days_overdue * 2)
        score += points
        factors.append({"factor": "overdue", "points": points, "detail": f"{days_overdue}d atrasado"})

    move_count = card.timeline_events.filter(event_type="CARD_MOVED").count()
    if move_count > 5:
        points = min(20, (move_count - 5) * 3)
        score += points
        factors.append({"factor": "excessive_movements", "points": points, "count": move_count})

    assignee_changes = (
        card.timeline_events.filter(event_type="CARD_ASSIGNED").count()
        + card.timeline_events.filter(event_type="CARD_UNASSIGNED").count()
    )
    if assignee_changes > 2:
        points = min(15, assignee_changes * 3)
        score += points
        factors.append({"factor": "assignee_churn", "points": points, "count": assignee_changes})

    if card.timeline_events.filter(event_type="CARD_REOPENED").exists():
        score += 20
        factors.append({"factor": "reopened", "points": 20})

    comm = analyze_communication(card)
    if comm.risks:
        points = min(15, len(comm.risks) * 5)
        score += points
        factors.append({"factor": "negative_communication", "points": points})

    checklist = analyze_checklists(card)
    if checklist.total_items and checklist.completion_pct < 50:
        points = 10
        score += points
        factors.append({"factor": "incomplete_checklist", "points": points, "pct": checklist.completion_pct})

    last_event = card.timeline_events.order_by("-event_timestamp").first()
    if last_event and (ref - last_event.event_timestamp) > timedelta(days=7) and not card.is_closed:
        points = 15
        score += points
        factors.append({"factor": "stagnant", "points": points})

    if comm.external_dependencies:
        points = min(10, len(comm.external_dependencies) * 5)
        score += points
        factors.append({"factor": "external_dependencies", "points": points})

    score = min(100, score)
    level = _score_to_level(score)

    return RiskAssessment(card_id=card.trello_id, score=score, level=level, factors=tuple(factors))


def assess_board_risk(
    *,
    board_trello_id: str | None = None,
    board_id: int | None = None,
) -> dict[str, Any]:
    """Assess risk for all active cards on a board."""
    ref = timezone.now()
    cards_qs = Card.objects.filter(is_removed=False, is_closed=False)
    if board_trello_id:
        cards_qs = cards_qs.filter(board__trello_id=board_trello_id)
    elif board_id:
        cards_qs = cards_qs.filter(board_id=board_id)

    assessments = [assess_card_risk(card, reference_time=ref) for card in cards_qs]
    high_risk = [a for a in assessments if a.score >= 50]

    return {
        "board_id": board_trello_id or board_id,
        "generated_at": ref.isoformat(),
        "total_cards": len(assessments),
        "high_risk_count": len(high_risk),
        "average_score": round(sum(a.score for a in assessments) / len(assessments), 1) if assessments else 0,
        "assessments": [
            {"card_id": a.card_id, "score": a.score, "level": a.level, "factors": list(a.factors)}
            for a in sorted(assessments, key=lambda x: x.score, reverse=True)[:30]
        ],
    }


def _score_to_level(score: int) -> str:
    for threshold, level in RISK_LEVELS:
        if score >= threshold:
            return level
    return "Baixo"
