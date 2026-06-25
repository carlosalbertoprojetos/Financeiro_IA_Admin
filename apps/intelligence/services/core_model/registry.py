from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apps.intelligence.services.core_model.models import WorkMetric


CANONICAL_ENTITY_TYPES = frozenset({
    "INCIDENT", "DELIVERY", "PROJECT", "INITIATIVE", "TASK_GROUP",
    "RISK_EVENT", "BOTTLENECK", "SLA_CONTRACT", "WORKLOAD_UNIT", "TASK",
})

TECHNICAL_METRICS = frozenset({
    "LEAD_TIME", "CYCLE_TIME", "RISK_SCORE", "SLA", "THROUGHPUT", "WIP",
})

SEMANTIC_METRICS = frozenset({
    "INCIDENT_RATE", "DELIVERY_SUCCESS_RATE", "RISK_EXPOSURE_INDEX",
    "TEAM_LOAD_BALANCE", "OPERATIONAL_EFFICIENCY", "BOTTLENECK_DENSITY",
    "SLA_BREACH_PROBABILITY",
})

CANONICAL_EVENTS = frozenset({
    "CARD_CREATED", "CARD_MOVED", "CARD_ASSIGNED", "CARD_UNASSIGNED",
    "CARD_REOPENED", "CARD_COMPLETED", "COMMENT_ADDED", "DUE_DATE_CHANGED",
    "LABEL_ADDED", "LABEL_REMOVED", "CHECKLIST_UPDATED", "CHECKLIST_STARTED",
    "CHECKLIST_COMPLETED", "CHECKLIST_ITEM_COMPLETED", "ATTACHMENT_ADDED",
    "BLOCKER_REGISTERED", "UNKNOWN",
})

RISK_TYPES = frozenset({
    "OVERDUE", "BLOCKED", "REWORK", "EXTERNAL_DEPENDENCY", "STAGNANT",
    "ASSIGNEE_CHURN", "HIGH_RISK_SCORE", "SLA_BREACH",
})

SEMANTIC_CATEGORIES = frozenset({
    "FINANCEIRO", "JURIDICO", "JURÍDICO", "OPERACIONAL", "COMERCIAL",
    "RH", "URGENTE", "AQUI", "CLIENTE", "PROJETO", "GERAL",
})

ENTITY_ALIASES: dict[str, str] = {
    "FAILURE": "INCIDENT",
    "TASK_COMPLETION": "DELIVERY",
    "COMPLETION": "DELIVERY",
    "BLOCKER": "BOTTLENECK",
    "WORK_ITEM": "TASK",
}

METRIC_SNAKE_MAP: dict[str, str] = {
    "incident_rate": "INCIDENT_RATE",
    "delivery_success_rate": "DELIVERY_SUCCESS_RATE",
    "risk_exposure_index": "RISK_EXPOSURE_INDEX",
    "team_load_balance_score": "TEAM_LOAD_BALANCE",
    "operational_efficiency_index": "OPERATIONAL_EFFICIENCY",
    "bottleneck_density": "BOTTLENECK_DENSITY",
    "sla_breach_probability": "SLA_BREACH_PROBABILITY",
}

METRIC_ALIASES: dict[str, str] = {
    "FAILURE_RATE": "INCIDENT_RATE",
    "TASK_COMPLETION_RATE": "DELIVERY_SUCCESS_RATE",
    "RISK_INDEX": "RISK_EXPOSURE_INDEX",
    "LOAD_BALANCE": "TEAM_LOAD_BALANCE",
    "EFFICIENCY": "OPERATIONAL_EFFICIENCY",
}


@dataclass
class ModelRegistry:
    entity_types: set[str] = field(default_factory=lambda: set(CANONICAL_ENTITY_TYPES))
    metrics: set[str] = field(default_factory=lambda: set(TECHNICAL_METRICS | SEMANTIC_METRICS))
    events: set[str] = field(default_factory=lambda: set(CANONICAL_EVENTS))
    risk_types: set[str] = field(default_factory=lambda: set(RISK_TYPES))
    categories: set[str] = field(default_factory=lambda: set(SEMANTIC_CATEGORIES))
    extensions: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_types": sorted(self.entity_types),
            "metrics": sorted(self.metrics),
            "events": sorted(self.events),
            "risk_types": sorted(self.risk_types),
            "categories": sorted(self.categories),
            "extensions": self.extensions,
        }

    def resolve_entity_type(self, raw: str) -> str | None:
        key = raw.upper().strip()
        if key in self.entity_types:
            return key
        alias = ENTITY_ALIASES.get(key)
        if alias and alias in self.entity_types:
            return alias
        return None

    def resolve_metric(self, raw: str) -> str | None:
        key = raw.upper().strip().replace(" ", "_")
        if key in self.metrics:
            return key
        alias = METRIC_ALIASES.get(key)
        if alias and alias in self.metrics:
            return alias
        return None

    def normalize_metric_key(self, key: str) -> str | None:
        """Resolve snake_case business metric keys to canonical names."""
        lower = key.lower().strip()
        if lower in METRIC_SNAKE_MAP:
            return METRIC_SNAKE_MAP[lower]
        upper = key.upper().replace(" ", "_")
        if upper in self.metrics:
            return upper
        return self.resolve_metric(upper)

    def register_extension(self, name: str, spec: dict[str, Any]) -> None:
        self.extensions[name] = spec

    def is_event_registered(self, event_type: str) -> bool:
        return event_type.upper() in self.events or event_type in self.events


REGISTRY = ModelRegistry()

METRIC_DEFINITIONS: list[WorkMetric] = [
    WorkMetric("LEAD_TIME", "query_engine", "hours", "Time from creation to completion"),
    WorkMetric("CYCLE_TIME", "query_engine", "hours", "Active work duration"),
    WorkMetric("RISK_SCORE", "query_engine", "score", "Operational risk 0-100"),
    WorkMetric("SLA", "query_engine", "compliance", "SLA compliance status"),
    WorkMetric("INCIDENT_RATE", "semantic", "percent", "Percentage of work items classified as incidents"),
    WorkMetric("DELIVERY_SUCCESS_RATE", "semantic", "percent", "Successful deliveries over total deliveries"),
    WorkMetric("RISK_EXPOSURE_INDEX", "semantic", "index", "Aggregate risk exposure"),
    WorkMetric("BOTTLENECK_DENSITY", "semantic", "percent", "Bottleneck concentration"),
]
