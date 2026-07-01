from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CanonicalTask:
    """
    Unified task representation across all integration providers.

    All adapters must map provider-specific records into this shape.
    """

    source_provider: str
    source_id: str
    title: str
    status: str
    project_id: str
    due_date: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    structured_description: dict[str, Any] = field(default_factory=dict)
    comments: list[dict[str, Any]] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    movements: list[dict[str, Any]] = field(default_factory=list)
    checklists: list[dict[str, Any]] = field(default_factory=list)
    attachments: list[dict[str, Any]] = field(default_factory=list)
    members: list[dict[str, Any]] = field(default_factory=list)
    assignees: list[dict[str, Any]] = field(default_factory=list)
    watchers: list[dict[str, Any]] = field(default_factory=list)
    labels: list[dict[str, Any]] = field(default_factory=list)
    dates: dict[str, Any] = field(default_factory=dict)
    derived_fields: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def metadata_with_canonical_fields(self) -> dict[str, Any]:
        enriched = dict(self.metadata)
        enriched.update(
            {
                "description": self.description,
                "structured_description": self.structured_description,
                "comments": self.comments,
                "actions": self.actions,
                "history": self.history,
                "movements": self.movements,
                "checklists": self.checklists,
                "attachments": self.attachments,
                "members": self.members,
                "assignees": self.assignees,
                "watchers": self.watchers,
                "labels": self.labels,
                "dates": self.dates,
                "derived_fields": self.derived_fields,
                "evidence": self.evidence,
                "raw": self.raw,
            }
        )
        return enriched

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_provider": self.source_provider,
            "source_id": self.source_id,
            "title": self.title,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "project_id": self.project_id,
            "metadata": self.metadata_with_canonical_fields(),
            "description": self.description,
            "structured_description": self.structured_description,
            "comments": self.comments,
            "actions": self.actions,
            "history": self.history,
            "movements": self.movements,
            "checklists": self.checklists,
            "attachments": self.attachments,
            "members": self.members,
            "assignees": self.assignees,
            "watchers": self.watchers,
            "labels": self.labels,
            "dates": self.dates,
            "derived_fields": self.derived_fields,
            "evidence": self.evidence,
            "raw": self.raw,
        }
