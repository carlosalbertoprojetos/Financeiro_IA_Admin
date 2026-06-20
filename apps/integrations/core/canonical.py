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

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_provider": self.source_provider,
            "source_id": self.source_id,
            "title": self.title,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "project_id": self.project_id,
            "metadata": self.metadata,
        }
