from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from django.dispatch import Signal

# Django signal — listeners subscribe without modifying SyncEngine.
sync_completed = Signal()


@dataclass(frozen=True)
class SyncCompletedEvent:
    """Payload emitted after a successful sync run."""

    provider: str
    connection_id: str
    project_id: str
    tasks_synced: int
    synced_at: datetime = field(default_factory=datetime.utcnow)
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "connection_id": self.connection_id,
            "project_id": self.project_id,
            "tasks_synced": self.tasks_synced,
            "synced_at": self.synced_at.isoformat(),
            "details": self.details,
        }


def emit_sync_completed(event: SyncCompletedEvent) -> None:
    sync_completed.send(
        sender=SyncCompletedEvent,
        event=event,
        **event.as_dict(),
    )
