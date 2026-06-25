from __future__ import annotations

import logging
from typing import Any

from django.core.cache import cache

from apps.intelligence.models import SemanticEntityCache
from apps.intelligence.services.semantic_layer.entities import BusinessEntity

logger = logging.getLogger(__name__)

CACHE_PREFIX = "eor:semantic:"
DEFAULT_TTL = 3600


def _entity_cache_key(board_id: str, card_id: str) -> str:
    return f"{CACHE_PREFIX}{board_id}:{card_id}"


def get_cached_entity(board_id: str, card_id: str) -> dict[str, Any] | None:
    key = _entity_cache_key(board_id, card_id)
    try:
        cached = cache.get(key)
        if cached:
            return cached
    except Exception:
        pass
    try:
        row = SemanticEntityCache.objects.filter(board_id=board_id, card_id=card_id).first()
        if row:
            return row.entity_data
    except Exception:
        pass
    return None


def set_cached_entity(board_id: str, entity: BusinessEntity, ttl: int = DEFAULT_TTL) -> None:
    data = entity.to_dict()
    key = _entity_cache_key(board_id, entity.card_id)
    try:
        cache.set(key, data, ttl)
    except Exception:
        pass
    try:
        SemanticEntityCache.objects.update_or_create(
            board_id=board_id,
            card_id=entity.card_id,
            defaults={
                "entity_type": entity.entity_type.value,
                "category": entity.category,
                "classification": entity.operational_intent,
                "entity_data": data,
            },
        )
    except Exception:
        logger.exception("Failed to persist semantic entity cache")


def resolve_entities_with_cache(
    board_id: str,
    entities: list[BusinessEntity],
    mapper_fn,
    cards,
    card_rows,
) -> list[BusinessEntity]:
    """Return entities using cache where available, mapping only uncached cards."""
    card_by_id = {c.trello_id: c for c in cards}
    row_by_id = {r.get("card_id", r.get("trello_id", "")): r for r in (card_rows or [])}
    resolved: list[BusinessEntity] = []

    for card in cards:
        cached = get_cached_entity(board_id, card.trello_id)
        if cached:
            resolved.append(_entity_from_dict(cached))
            continue
        entity = mapper_fn(card, row=row_by_id.get(card.trello_id, {}))
        set_cached_entity(board_id, entity)
        resolved.append(entity)

    return resolved


def _entity_from_dict(data: dict[str, Any]) -> BusinessEntity:
    from apps.intelligence.services.semantic_layer.entities import EntityStatus, EntityType, Severity

    return BusinessEntity(
        entity_id=data["entity_id"],
        entity_type=EntityType(data["entity_type"]),
        category=data.get("category", "GERAL"),
        severity=Severity(data.get("severity", "LOW")),
        status=EntityStatus(data.get("status", "ACTIVE")),
        title=data.get("title", ""),
        card_id=data.get("card_id", data["entity_id"]),
        related_members=data.get("related_members", []),
        risk_flags=data.get("risk_flags", []),
        labels=data.get("labels", []),
        risk_score=float(data.get("risk_score", 0)),
        operational_intent=data.get("operational_intent", ""),
        confidence=float(data.get("confidence", 0)),
        metadata=data.get("metadata", {}),
    )
