from __future__ import annotations

from typing import Any

from apps.intelligence.services.semantic_layer.entities import EntityType
from integrations.trello.models import Card

INCIDENT_INTENTS = frozenset({"incident_response", "unblock", "escalation"})
DELIVERY_INTENTS = frozenset({"fulfillment", "closure", "handoff"})
PROJECT_INTENTS = frozenset({"planning", "execution", "tracking"})


def classify_operational_intent(card: Card, entity_type: EntityType) -> str:
    """Classify the operational intent of work represented by a card."""
    title = (card.title or "").lower()
    if entity_type == EntityType.INCIDENT:
        if "bloquei" in title:
            return "unblock"
        if "urgente" in title or "atrasad" in title:
            return "escalation"
        return "incident_response"
    if entity_type == EntityType.DELIVERY:
        if "deploy" in title:
            return "handoff"
        return "fulfillment"
    if entity_type == EntityType.PROJECT:
        return "execution"
    if entity_type == EntityType.RISK_EVENT:
        return "mitigation"
    if entity_type == EntityType.BOTTLENECK:
        return "flow_recovery"
    if entity_type == EntityType.SLA_CONTRACT:
        return "sla_compliance"
    return "operational_task"


def detect_risk_flags(card: Card, row: dict[str, Any] | None = None) -> list[str]:
    """Detect business risk flags from card state and metrics."""
    row = row or {}
    flags: list[str] = []
    title = (card.title or "").lower()

    if card.due_at and not card.completed_at:
        from django.utils import timezone

        if card.due_at < timezone.now():
            flags.append("overdue")
    if "depend" in title or "extern" in title:
        flags.append("external_dependency")
    if "retrabalho" in title or "reopen" in title.lower():
        flags.append("rework")
    if row.get("risk_level") in ("Alto", "Crítico", "Critico"):
        flags.append("high_risk")
    if float(row.get("risk_score", 0)) >= 50:
        flags.append("elevated_risk_score")
    status = (card.status or "").lower()
    if "bloqueado" in status:
        flags.append("blocked")
    return flags


def detect_work_type(card: Card) -> str:
    """Detect automatic work type classification."""
    title = (card.title or "").lower()
    if any(k in title for k in ("atrasad", "erro", "bloquei", "incidente")):
        return "INCIDENT"
    from django.utils import timezone

    if card.due_at and not card.completed_at and card.due_at < timezone.now():
        return "INCIDENT"
    if any(k in title for k in ("conclu", "deploy", "entreg", "finaliz")):
        return "DELIVERY"
    if card.is_closed or card.completed_at:
        return "DELIVERY"
    if any(k in title for k in ("depend", "risco", "extern")):
        return "RISK"
    from apps.intelligence.services.report_query.domain.title_parser import extract_prefix

    if extract_prefix(card.title or ""):
        return "PROJECT"
    return "TASK"
