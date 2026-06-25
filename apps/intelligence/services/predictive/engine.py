"""Predictive engine — estimates delay, block, and completion probability."""

from __future__ import annotations

from datetime import datetime, timedelta
from statistics import mean
from typing import Any

from django.utils import timezone

from analytics.adapters import load_board_records
from apps.intelligence.domain.entities import PredictiveResult
from apps.intelligence.services.risk_engine.scorer import assess_card_risk
from integrations.trello.models import Card


def predict_card(card: Card, *, reference_time: datetime | None = None) -> PredictiveResult:
    """Generate predictive assessment for a card."""
    ref = reference_time or timezone.now()
    risk = assess_card_risk(card, reference_time=ref)

    delay_prob = _estimate_delay_probability(card, risk.score, ref)
    block_prob = _estimate_block_probability(card, risk.score)
    estimated_completion = _estimate_completion_date(card, ref)
    escalation = risk.score >= 60 or delay_prob >= 0.7
    operational_risk = risk.level
    sla_risk = _assess_sla_risk(card, ref)

    return PredictiveResult(
        card_id=card.trello_id,
        delay_probability=round(delay_prob, 2),
        block_probability=round(block_prob, 2),
        estimated_completion=estimated_completion,
        escalation_needed=escalation,
        operational_risk=operational_risk,
        sla_risk=sla_risk,
    )


def predict_board(
    *,
    board_trello_id: str | None = None,
    board_id: int | None = None,
) -> dict[str, Any]:
    """Generate predictive assessments for all open cards."""
    ref = timezone.now()
    cards_qs = Card.objects.filter(is_removed=False, is_closed=False)
    if board_trello_id:
        cards_qs = cards_qs.filter(board__trello_id=board_trello_id)
    elif board_id:
        cards_qs = cards_qs.filter(board_id=board_id)

    predictions = [predict_card(card, reference_time=ref) for card in cards_qs]
    high_delay = [p for p in predictions if p.delay_probability >= 0.6]

    return {
        "board_id": board_trello_id or board_id,
        "generated_at": ref.isoformat(),
        "total_predictions": len(predictions),
        "high_delay_risk": len(high_delay),
        "predictions": [
            {
                "card_id": p.card_id,
                "delay_probability": p.delay_probability,
                "block_probability": p.block_probability,
                "estimated_completion": p.estimated_completion.isoformat() if p.estimated_completion else None,
                "escalation_needed": p.escalation_needed,
                "operational_risk": p.operational_risk,
                "sla_risk": p.sla_risk,
            }
            for p in sorted(predictions, key=lambda x: x.delay_probability, reverse=True)[:30]
        ],
    }


def _estimate_delay_probability(card: Card, risk_score: int, ref: datetime) -> float:
    prob = risk_score / 100 * 0.6
    if card.due_at and not card.completed_at:
        days_remaining = (card.due_at - ref).total_seconds() / 86400
        if days_remaining < 0:
            prob = max(prob, 0.9)
        elif days_remaining < 2:
            prob = max(prob, 0.7)
        elif days_remaining < 5:
            prob = max(prob, 0.4)
    return min(1.0, prob)


def _estimate_block_probability(card: Card, risk_score: int) -> float:
    blocker_events = card.timeline_events.filter(
        event_type__in=("BLOCKER_REGISTERED", "COMMENT_ADDED")
    ).count()
    prob = risk_score / 100 * 0.4
    if blocker_events > 0:
        prob = min(1.0, prob + 0.2)
    return prob


def _estimate_completion_date(card: Card, ref: datetime) -> datetime | None:
    if card.completed_at:
        return card.completed_at

    cards, _ = load_board_records(board_id=card.board_id, include_removed=False)
    completed = [c for c in cards if c.completed_at and c.created_at]
    if not completed:
        if card.due_at:
            return card.due_at
        return ref + timedelta(days=7)

    lead_hours = [
        (c.completed_at - c.created_at).total_seconds() / 3600
        for c in completed
        if c.completed_at and c.created_at
    ]
    if not lead_hours:
        return ref + timedelta(days=7)

    avg_hours = mean(lead_hours)
    start = card.created_at or ref
    return start + timedelta(hours=avg_hours)


def _assess_sla_risk(card: Card, ref: datetime) -> str:
    if not card.due_at:
        return "N/A"
    if card.completed_at:
        return "Cumprido" if card.completed_at <= card.due_at else "Violado"
    if card.due_at < ref:
        return "Violado"
    days_left = (card.due_at - ref).days
    if days_left <= 2:
        return "Em risco"
    return "No prazo"
