from __future__ import annotations

from typing import Any

from apps.intelligence.services.eql.ast import EQLQuery
from apps.intelligence.services.semantic_layer.entities import SemanticReport
from apps.intelligence.services.semantic_layer.entity_mapper import (
    filter_entities,
    map_card_to_entity,
    map_cards_to_entities,
)
from apps.intelligence.services.semantic_layer.cache import resolve_entities_with_cache
from apps.intelligence.services.semantic_layer.domain_intelligence import generate_domain_insights
from apps.intelligence.services.semantic_layer.metrics import compute_business_metrics, summarize_entities
from apps.intelligence.services.observability.ai_trace import trace_recommendations
from apps.intelligence.services.observability.semantic_trace import infer_classification_rules, trace_entity_classification
from integrations.trello.models import Card


def apply_semantic_layer(
    raw_output: dict[str, Any],
    *,
    cards: list[Card] | None = None,
    semantic_filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Transform raw query engine output into business semantic report.
    Does NOT execute queries — only maps and enriches existing data.
    """
    board_id = raw_output.get("summary", {}).get("board_id", "")
    card_rows = raw_output.get("cards", [])
    semantic_filters = semantic_filters or raw_output.get("semantic_filters", {})

    if cards is None:
        card_ids = [r.get("card_id", r.get("trello_id")) for r in card_rows if r.get("card_id") or r.get("trello_id")]
        cards = list(
            Card.objects.filter(trello_id__in=card_ids, board__trello_id=board_id).select_related("board_list").prefetch_related("assignees")
        ) if card_ids else []

    entities = resolve_entities_with_cache(
        board_id,
        [],
        map_card_to_entity,
        cards,
        card_rows,
    ) if cards else map_cards_to_entities(cards or [], card_rows)

    if semantic_filters:
        entities = filter_entities(entities, semantic_filters)

    for entity in entities:
        trace_entity_classification(
            entity.card_id,
            entity.title,
            entity.entity_type.value,
            rules=infer_classification_rules(
                entity.title,
                overdue=entity.status.value == "DELAYED",
                closed=entity.status.value == "COMPLETED",
            ),
            severity=entity.severity.value,
            status=entity.status.value,
            risk_score=entity.risk_score,
        )

    business_metrics = compute_business_metrics(entities)
    domain_insights = generate_domain_insights(entities)
    if domain_insights:
        trace_recommendations(domain_insights)
    entity_summary = summarize_entities(entities)

    semantic_report = SemanticReport(
        entities=entities,
        business_metrics=business_metrics,
        domain_insights=domain_insights,
        entity_summary=entity_summary,
    )

    enriched = dict(raw_output)
    enriched["semantic"] = semantic_report.to_dict()
    enriched["business_metrics"] = business_metrics
    enriched["domain_insights"] = domain_insights
    enriched["entities"] = [e.to_dict() for e in entities]
    enriched["recommendations"] = list(raw_output.get("recommendations", [])) + domain_insights[:3]
    return enriched
