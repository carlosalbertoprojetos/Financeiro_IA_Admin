from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class IngestionCursor:
    """Provider-scoped sync cursor stored between incremental runs."""

    provider: str
    connection_id: str
    cursor: dict[str, Any] = field(default_factory=dict)
    updated_at: datetime | None = None

    def get(self, key: str, default: Any = None) -> Any:
        return self.cursor.get(key, default)

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "connection_id": self.connection_id,
            "cursor": self.cursor,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
