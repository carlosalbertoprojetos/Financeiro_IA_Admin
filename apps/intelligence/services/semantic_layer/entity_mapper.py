from __future__ import annotations

import re
from typing import Any

from django.utils import timezone

from apps.intelligence.services.report_query.domain.title_parser import extract_prefix
from apps.intelligence.services.description_intelligence.summary import analyze_card_description
from apps.intelligence.services.semantic_layer.entities import (
    BusinessEntity,
    EntityStatus,
    EntityType,
    RiskLevel,
    Severity,
)
from apps.intelligence.services.semantic_layer.enrichment import classify_operational_intent, detect_risk_flags
from integrations.trello.models import Card

INCIDENT_KEYWORDS = re.compile(
    r"\b(atrasad|atraso|erro|bloquei|retrabalho|urgente|falha|incidente|problema)\b",
    re.I,
)
DELIVERY_KEYWORDS = re.compile(
    r"\b(conclu|finaliz|deploy|envio|entreg|completed|done|feito)\b",
    re.I,
)
RISK_KEYWORDS = re.compile(
    r"\b(depend[eê]ncia|externo|recorrente|sobrecarga|risco|critical)\b",
    re.I,
)


def map_card_to_entity(card: Card, *, row: dict[str, Any] | None = None) -> BusinessEntity:
    """Transform a card (+ optional metric row) into a business entity."""
    row = row or {}
    title = card.title or ""
    description = analyze_card_description(card)
    category = _resolve_category(card, title, description)
    entity_type = _infer_entity_type(card, title)
    status = _infer_entity_status(card, title)
    severity = _infer_severity(card, row, status)
    members = _extract_members(card, row)
    risk_flags = [*detect_risk_flags(card, row), *_description_risk_flags(description)]
    intent = classify_operational_intent(card, entity_type)
    risk_score = float(row.get("risk_score", 0))

    return BusinessEntity(
        entity_id=card.trello_id,
        entity_type=entity_type,
        category=category,
        severity=severity,
        status=status,
        title=title,
        card_id=card.trello_id,
        related_members=members,
        risk_flags=risk_flags,
        labels=_extract_labels(card, row),
        risk_score=risk_score,
        operational_intent=intent,
        confidence=_confidence(entity_type, title, card),
        metadata={
            "list": getattr(card.board_list, "name", None) if card.board_list_id else None,
            "due_at": card.due_at.isoformat() if card.due_at else None,
            "completed_at": card.completed_at.isoformat() if card.completed_at else None,
            "description_intelligence": {
                "quality_score": description["quality"]["score"],
                "classifications": description["classifications"],
                "entities": description["entities"],
                "events": description["events"],
                "expanded_summary": description["expanded_summary"],
            },
        },
    )


def map_cards_to_entities(cards: list[Card], card_rows: list[dict[str, Any]] | None = None) -> list[BusinessEntity]:
    row_by_id = {r.get("card_id", r.get("trello_id", "")): r for r in (card_rows or [])}
    return [map_card_to_entity(c, row=row_by_id.get(c.trello_id, {})) for c in cards]


def filter_entities(
    entities: list[BusinessEntity],
    semantic_filters: dict[str, Any],
) -> list[BusinessEntity]:
    """Apply semantic filters to mapped entities (post-query, no DB execution)."""
    result = entities
    if not semantic_filters:
        return result

    entity_types = semantic_filters.get("entity_type", {})
    if entity_types:
        values = {v.upper() for v in entity_types.get("values", [])}
        result = [e for e in result if e.entity_type.value in values]

    category = semantic_filters.get("category")
    if category:
        cat_val = category.upper() if isinstance(category, str) else category.get("value", "").upper()
        if cat_val:
            result = [e for e in result if e.category.upper() == cat_val]

    risk_level = semantic_filters.get("risk_level")
    if isinstance(risk_level, dict) and "value" in risk_level:
        threshold = _risk_level_to_score(str(risk_level.get("value", "HIGH")))
        op = risk_level.get("op", ">=")
        result = [e for e in result if _compare_risk(e.risk_score, op, threshold)]

    entity_status = semantic_filters.get("entity_status")
    if entity_status:
        statuses = entity_status if isinstance(entity_status, list) else entity_status.get("values", [])
        status_set = {s.upper() for s in statuses}
        result = [e for e in result if e.status.value in status_set]

    return result


def _resolve_category(card: Card, title: str, description: dict[str, Any] | None = None) -> str:
    prefix = extract_prefix(title)
    if prefix:
        return prefix
    labels = card.labels or []
    if labels and isinstance(labels[0], dict):
        return str(labels[0].get("name", "GERAL")).upper()
    if description:
        classifications = description.get("classifications") or []
        if classifications and classifications[0].get("category") != "Outra":
            return str(classifications[0]["category"]).upper()
    return "GERAL"


def _description_risk_flags(description: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    summary = description.get("expanded_summary") or {}
    if summary.get("bloqueios"):
        flags.append("description_blocker")
    if summary.get("dependencias"):
        flags.append("description_dependency")
    if summary.get("impacto"):
        flags.append("description_impact")
    return flags


def _infer_entity_type(card: Card, title: str) -> EntityType:
    now = timezone.now()
    if card.is_closed or card.completed_at:
        if DELIVERY_KEYWORDS.search(title) or card.completed_at:
            return EntityType.DELIVERY
    if INCIDENT_KEYWORDS.search(title):
        return EntityType.INCIDENT
    if card.due_at and not card.completed_at and card.due_at < now:
        return EntityType.INCIDENT
    if RISK_KEYWORDS.search(title):
        return EntityType.RISK_EVENT
    if extract_prefix(title):
        return EntityType.PROJECT
    move_heavy = getattr(card, "timeline_events", None)
    if move_heavy and move_heavy.filter(event_type="CARD_MOVED").count() > 5:
        return EntityType.BOTTLENECK
    if card.due_at:
        return EntityType.SLA_CONTRACT
    if card.assignees.exists() if hasattr(card, "assignees") else False:
        return EntityType.WORKLOAD_UNIT
    return EntityType.TASK


def _infer_entity_status(card: Card, title: str) -> EntityStatus:
    if card.is_closed and card.completed_at:
        return EntityStatus.COMPLETED
    status_lower = (card.status or "").lower()
    if "bloqueado" in status_lower or "blocked" in status_lower:
        return EntityStatus.BLOCKED
    if "cancel" in status_lower:
        return EntityStatus.CANCELLED
    now = timezone.now()
    if card.due_at and not card.completed_at and card.due_at < now:
        return EntityStatus.DELAYED
    if INCIDENT_KEYWORDS.search(title):
        return EntityStatus.DELAYED
    return EntityStatus.ACTIVE


def _infer_severity(card: Card, row: dict[str, Any], status: EntityStatus) -> Severity:
    score = float(row.get("risk_score", 0))
    if score >= 75 or status == EntityStatus.DELAYED and score >= 50:
        return Severity.CRITICAL
    if score >= 50 or status in (EntityStatus.DELAYED, EntityStatus.BLOCKED):
        return Severity.HIGH
    if score >= 25:
        return Severity.MEDIUM
    return Severity.LOW


def _extract_members(card: Card, row: dict[str, Any]) -> list[str]:
    if row.get("assignees"):
        return list(row["assignees"])
    if hasattr(card, "assignees"):
        return [m.full_name or m.username for m in card.assignees.all()]
    return []


def _extract_labels(card: Card, row: dict[str, Any]) -> list[str]:
    if row.get("labels"):
        return list(row["labels"])
    labels = card.labels or []
    return [lbl.get("name", "") for lbl in labels if isinstance(lbl, dict)]


def _confidence(entity_type: EntityType, title: str, card: Card) -> float:
    score = 0.5
    if INCIDENT_KEYWORDS.search(title) or DELIVERY_KEYWORDS.search(title):
        score += 0.25
    if extract_prefix(title):
        score += 0.15
    if card.completed_at or card.due_at:
        score += 0.1
    return min(1.0, score)


def _risk_level_to_score(level: str) -> float:
    return {"LOW": 25, "MODERATE": 40, "MEDIUM": 40, "HIGH": 50, "CRITICAL": 75}.get(level.upper(), 50)


def _compare_risk(value: float, op: str, threshold: float) -> bool:
    if op == ">=":
        return value >= threshold
    if op == "<=":
        return value <= threshold
    if op == ">":
        return value > threshold
    if op == "<":
        return value < threshold
    return value == threshold
