from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EntityType(str, Enum):
    PROJECT = "PROJECT"
    INITIATIVE = "INITIATIVE"
    TASK_GROUP = "TASK_GROUP"
    INCIDENT = "INCIDENT"
    DELIVERY = "DELIVERY"
    RISK_EVENT = "RISK_EVENT"
    BOTTLENECK = "BOTTLENECK"
    SLA_CONTRACT = "SLA_CONTRACT"
    WORKLOAD_UNIT = "WORKLOAD_UNIT"
    TASK = "TASK"


class EntityStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    DELAYED = "DELAYED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class BusinessEntity:
    entity_id: str
    entity_type: EntityType
    category: str
    severity: Severity
    status: EntityStatus
    title: str
    card_id: str
    related_members: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    risk_score: float = 0.0
    operational_intent: str = ""
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "category": self.category,
            "severity": self.severity.value,
            "status": self.status.value,
            "title": self.title,
            "card_id": self.card_id,
            "related_members": self.related_members,
            "risk_flags": self.risk_flags,
            "labels": self.labels,
            "risk_score": self.risk_score,
            "operational_intent": self.operational_intent,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass
class SemanticReport:
    entities: list[BusinessEntity]
    business_metrics: dict[str, Any]
    domain_insights: list[str]
    entity_summary: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "entities": [e.to_dict() for e in self.entities],
            "business_metrics": self.business_metrics,
            "domain_insights": self.domain_insights,
            "entity_summary": self.entity_summary,
        }
