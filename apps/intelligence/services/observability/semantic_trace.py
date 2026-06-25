from __future__ import annotations

from typing import Any

from apps.intelligence.services.observability.context import get_collector


def trace_entity_classification(
    card_id: str,
    title: str,
    entity_type: str,
    *,
    rules: list[str],
    severity: str = "",
    status: str = "",
    risk_score: float = 0,
) -> None:
    """Record why a card was classified as a business entity."""
    collector = get_collector()
    if not collector:
        return
    collector.record_semantic_mapping(
        card_id,
        entity_type,
        rules,
        title=title[:200],
        severity=severity,
        status=status,
        risk_score=risk_score,
    )
    if entity_type == "INCIDENT":
        collector.record_rule("incident_classification", "semantic_layer", f"classified {card_id} as INCIDENT", signals=rules)
    if risk_score >= 50:
        collector.record_rule("high_risk_threshold", "semantic_layer", f"risk_score={risk_score} >= 50", card_id=card_id)


def infer_classification_rules(title: str, *, overdue: bool = False, closed: bool = False) -> list[str]:
    rules: list[str] = []
    lower = title.lower()
    if overdue:
        rules.append("due_date_passed")
    if any(k in lower for k in ("atrasad", "erro", "bloquei", "incidente")):
        rules.append("title_keyword_match")
    if closed:
        rules.append("card_completed")
    if any(k in lower for k in ("conclu", "deploy", "entreg")):
        rules.append("delivery_keyword_match")
    return rules or ["default_classification"]
