from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkItemKind(str, Enum):
    CARD = "CARD"
    EVENT = "EVENT"
    ENRICHMENT = "ENRICHMENT"


@dataclass
class WorkItem:
    """Canonical representation of an operational work unit."""

    id: str
    kind: WorkItemKind
    title: str = ""
    board_id: str = ""
    status: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "title": self.title,
            "board_id": self.board_id,
            "status": self.status,
            "metadata": self.metadata,
        }


@dataclass
class WorkEvent:
    """Canonical timeline event."""

    id: str
    event_type: str
    timestamp: str
    actor: str = ""
    work_item_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "work_item_id": self.work_item_id,
            "payload": self.payload,
        }


@dataclass
class WorkEntity:
    """Canonical business entity derived from work items."""

    id: str
    entity_type: str
    category: str
    status: str
    severity: str
    source_work_item_id: str
    aliases: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "category": self.category,
            "status": self.status,
            "severity": self.severity,
            "source_work_item_id": self.source_work_item_id,
            "aliases": self.aliases,
            "metadata": self.metadata,
        }


@dataclass
class WorkMetric:
    """Canonical metric definition."""

    name: str
    layer: str
    unit: str
    description: str = ""
    aliases: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "layer": self.layer,
            "unit": self.unit,
            "description": self.description,
            "aliases": self.aliases,
        }


@dataclass
class WorkRelationship:
    """Canonical relationship between work entities."""

    source_id: str
    target_id: str
    relationship_type: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type,
            "metadata": self.metadata,
        }
