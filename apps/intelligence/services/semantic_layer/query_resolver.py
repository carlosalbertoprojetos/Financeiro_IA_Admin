from __future__ import annotations

from typing import Any

from apps.intelligence.services.eql.ast import EQLQuery

SEMANTIC_FILTER_KEYS = frozenset({
    "entity_type", "category", "risk_level", "entity_status",
})

ENTITY_TYPE_TO_TECHNICAL = {
    "INCIDENT": {
        "status": {"values": ["atrasado", "bloqueado"], "operator": "OR"},
    },
    "DELIVERY": {
        "status": {"values": ["concluido"], "operator": "OR"},
    },
    "PROJECT": {
        "title_prefix": "AUTO",
    },
}

RISK_LEVEL_THRESHOLDS = {
    "LOW": 25,
    "MODERATE": 40,
    "MEDIUM": 40,
    "HIGH": 50,
    "CRITICAL": 75,
}


def extract_semantic_filters(query: EQLQuery) -> dict[str, Any]:
    """Extract semantic filters from AST (stored separately from technical filters)."""
    semantic: dict[str, Any] = {}
    for key in SEMANTIC_FILTER_KEYS:
        if key in query.filters:
            semantic[key] = query.filters.pop(key)
    return semantic


def resolve_semantic_to_technical(query: EQLQuery) -> tuple[EQLQuery, dict[str, Any]]:
    """
    Translate semantic EQL filters into technical filters for Query Engine.
    Semantic filters are preserved separately for post-execution entity filtering.
    """
    semantic = extract_semantic_filters(query)

    if semantic.get("category"):
        cat = semantic["category"]
        cat_val = cat if isinstance(cat, str) else cat.get("value", "")
        if cat_val and "title_prefix" not in query.filters:
            query.filters["title_prefix"] = cat_val.upper()
        if cat_val and "labels" not in query.filters:
            query.filters["labels"] = {"values": [cat_val], "operator": "OR"}

    entity_type = semantic.get("entity_type", {})
    types = entity_type.get("values", []) if isinstance(entity_type, dict) else []
    for et in types:
        mapping = ENTITY_TYPE_TO_TECHNICAL.get(et.upper(), {})
        for tech_key, tech_val in mapping.items():
            if tech_key not in query.filters:
                query.filters[tech_key] = tech_val

    risk_level = semantic.get("risk_level")
    if isinstance(risk_level, dict) and "value" in risk_level:
        threshold = RISK_LEVEL_THRESHOLDS.get(str(risk_level["value"]).upper(), 50)
        if "risk_score" not in query.filters:
            query.filters["risk_score"] = {"op": risk_level.get("op", ">="), "value": threshold}

    entity_status = semantic.get("entity_status")
    if entity_status:
        statuses = entity_status if isinstance(entity_status, list) else entity_status.get("values", [])
        status_map = {
            "ACTIVE": ["aberto", "em andamento"],
            "DELAYED": ["atrasado"],
            "BLOCKED": ["bloqueado"],
            "COMPLETED": ["concluido"],
        }
        tech_statuses: list[str] = []
        for s in statuses:
            tech_statuses.extend(status_map.get(s.upper(), [s.lower()]))
        if tech_statuses and "status" not in query.filters:
            query.filters["status"] = {"values": tech_statuses, "operator": "OR"}

    return query, semantic
