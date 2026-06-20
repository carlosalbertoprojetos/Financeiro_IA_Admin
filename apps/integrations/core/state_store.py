from dataclasses import dataclass
from datetime import datetime
from typing import Any

from django.utils import timezone

from apps.integrations.models import IntegrationState


@dataclass
class IntegrationStateSnapshot:
    """Integration sync state for a provider connection."""

    provider: str
    connection_id: str
    last_sync_cursor: dict[str, Any]
    last_sync_time: datetime | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "connection_id": self.connection_id,
            "last_sync_cursor": self.last_sync_cursor,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
        }


def get_last_cursor(provider: str, connection_id: str) -> IntegrationStateSnapshot:
    """
    Return the stored sync state for a provider connection.

    When no state exists yet, returns an empty cursor and null last_sync_time.
    """
    record = IntegrationState.objects.filter(
        provider=provider,
        connection_id=connection_id,
    ).first()

    if record is None:
        return IntegrationStateSnapshot(
            provider=provider,
            connection_id=connection_id,
            last_sync_cursor={},
            last_sync_time=None,
        )

    return IntegrationStateSnapshot(
        provider=record.provider,
        connection_id=str(record.connection_id),
        last_sync_cursor=record.last_sync_cursor or {},
        last_sync_time=record.last_sync_time,
    )


def update_cursor(
    provider: str,
    connection_id: str,
    cursor: dict[str, Any],
    *,
    sync_time: datetime | None = None,
) -> IntegrationStateSnapshot:
    """Persist the latest sync cursor and timestamp after successful processing."""
    resolved_time = sync_time or timezone.now()

    record, _ = IntegrationState.objects.update_or_create(
        provider=provider,
        connection_id=connection_id,
        defaults={
            "last_sync_cursor": cursor,
            "last_sync_time": resolved_time,
        },
    )

    return IntegrationStateSnapshot(
        provider=record.provider,
        connection_id=str(record.connection_id),
        last_sync_cursor=record.last_sync_cursor or {},
        last_sync_time=record.last_sync_time,
    )
