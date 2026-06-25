from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from apps.intelligence.services.semantic_layer.entities import BusinessEntity, EntityStatus, EntityType


def compute_business_metrics(entities: list[BusinessEntity]) -> dict[str, Any]:
    """Compute semantic KPIs from mapped business entities."""
    total = len(entities) or 1
    incidents = [e for e in entities if e.entity_type == EntityType.INCIDENT]
    deliveries = [e for e in entities if e.entity_type == EntityType.DELIVERY]
    risks = [e for e in entities if e.entity_type in (EntityType.RISK_EVENT, EntityType.INCIDENT)]
    bottlenecks = [e for e in entities if e.entity_type == EntityType.BOTTLENECK]

    completed_deliveries = [e for e in deliveries if e.status == EntityStatus.COMPLETED]
    failed_deliveries = [e for e in deliveries if e.status in (EntityStatus.DELAYED, EntityStatus.BLOCKED)]

    incident_rate = round(len(incidents) / total * 100, 1)
    delivery_success = round(len(completed_deliveries) / max(len(deliveries), 1) * 100, 1)
    avg_risk = round(sum(e.risk_score for e in entities) / total, 1)
    risk_exposure = round(min(100, avg_risk + len(risks) / total * 20), 1)

    member_load = Counter(m for e in entities for m in e.related_members)
    load_values = list(member_load.values()) or [0]
    load_balance = _load_balance_score(load_values)

    active = [e for e in entities if e.status == EntityStatus.ACTIVE]
    efficiency = round(len(completed_deliveries) / max(len(active) + len(completed_deliveries), 1) * 100, 1)

    bottleneck_density = round(len(bottlenecks) / total * 100, 1)

    sla_entities = [e for e in entities if e.entity_type == EntityType.SLA_CONTRACT or e.metadata.get("due_at")]
    overdue = [e for e in sla_entities if e.status == EntityStatus.DELAYED]
    sla_breach_prob = round(len(overdue) / max(len(sla_entities), 1) * 100, 1)

    return {
        "incident_rate": {"value": incident_rate, "count": len(incidents), "unit": "percent"},
        "delivery_success_rate": {
            "value": delivery_success,
            "completed": len(completed_deliveries),
            "failed": len(failed_deliveries),
            "unit": "percent",
        },
        "risk_exposure_index": {"value": risk_exposure, "avg_risk_score": avg_risk, "unit": "index"},
        "team_load_balance_score": {"value": load_balance, "members": len(member_load), "unit": "score"},
        "operational_efficiency_index": {"value": efficiency, "unit": "percent"},
        "bottleneck_density": {"value": bottleneck_density, "count": len(bottlenecks), "unit": "percent"},
        "sla_breach_probability": {"value": sla_breach_prob, "overdue": len(overdue), "unit": "percent"},
    }


def summarize_entities(entities: list[BusinessEntity]) -> dict[str, int]:
    summary: dict[str, int] = defaultdict(int)
    for e in entities:
        summary[e.entity_type.value] += 1
        summary[f"status_{e.status.value}"] += 1
    return dict(summary)


def _load_balance_score(loads: list[int]) -> float:
    if not loads:
        return 100.0
    avg = sum(loads) / len(loads)
    if avg == 0:
        return 100.0
    variance = sum((x - avg) ** 2 for x in loads) / len(loads)
    normalized = min(100, max(0, 100 - (variance / avg) * 10))
    return round(normalized, 1)
