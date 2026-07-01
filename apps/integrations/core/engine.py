import logging
from dataclasses import dataclass, field
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.integrations.core.canonical import CanonicalTask
from apps.integrations.core.events import SyncCompletedEvent, emit_sync_completed
from apps.integrations.core.exceptions import ConnectionNotFoundError
from apps.integrations.core.registry import IntegrationRegistry, registry
from apps.integrations.models import CanonicalTaskRecord, IntegrationConnection

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    provider: str
    connection_id: str
    project_id: str
    tasks_synced: int
    synced_at: str = field(default_factory=lambda: timezone.now().isoformat())
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "connection_id": self.connection_id,
            "project_id": self.project_id,
            "tasks_synced": self.tasks_synced,
            "synced_at": self.synced_at,
            "details": self.details,
        }


class SyncEngine:
    """
    Central orchestrator for integration syncs.

    Resolves adapter from registry, runs provider pipeline, persists canonical
    tasks, and emits sync_completed — without provider-specific branching.
    """

    def __init__(self, integration_registry: IntegrationRegistry | None = None) -> None:
        self._registry = integration_registry or registry

    def run(self, provider: str, connection_id: str) -> SyncResult:
        connection = self._load_connection(connection_id, provider)
        adapter = self._registry.get(provider)

        logger.info(
            "Starting sync provider=%s connection_id=%s project_id=%s",
            provider,
            connection_id,
            connection.project_id,
        )

        tasks = adapter.sync(connection)
        saved_count = self._persist_tasks(connection, tasks)
        connection.mark_synced()

        extra_details = getattr(adapter, "last_sync_details", None) or {}
        result = SyncResult(
            provider=provider,
            connection_id=str(connection.pk),
            project_id=connection.project_id,
            tasks_synced=saved_count,
            details=extra_details if isinstance(extra_details, dict) else {},
        )

        emit_sync_completed(
            SyncCompletedEvent(
                provider=provider,
                connection_id=str(connection.pk),
                project_id=connection.project_id,
                tasks_synced=saved_count,
                synced_at=timezone.now(),
                details=result.details,
            )
        )

        logger.info(
            "Sync completed provider=%s connection_id=%s tasks=%d",
            provider,
            connection_id,
            saved_count,
        )
        return result

    def _load_connection(self, connection_id: str, provider: str) -> IntegrationConnection:
        try:
            connection = IntegrationConnection.objects.get(pk=connection_id, provider=provider)
        except IntegrationConnection.DoesNotExist as exc:
            raise ConnectionNotFoundError(connection_id) from exc
        return connection

    @transaction.atomic
    def _persist_tasks(
        self,
        connection: IntegrationConnection,
        tasks: list[CanonicalTask],
    ) -> int:
        saved = 0
        for task in tasks:
            CanonicalTaskRecord.objects.update_or_create(
                connection=connection,
                source_provider=task.source_provider,
                source_id=task.source_id,
                defaults={
                    "title": task.title,
                    "status": task.status,
                    "due_date": task.due_date,
                    "project_id": task.project_id,
                    "metadata": task.metadata_with_canonical_fields(),
                },
            )
            saved += 1
        return saved
