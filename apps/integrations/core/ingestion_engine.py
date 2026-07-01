import logging
from dataclasses import dataclass, field
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.integrations.core.canonical import CanonicalTask
from apps.integrations.core.events import SyncCompletedEvent, emit_sync_completed
from apps.integrations.core.exceptions import ConnectionNotFoundError
from apps.integrations.core.ingestion_state import IngestionCursor
from apps.integrations.core.queue import (
    IntegrationEvent,
    IntegrationQueueBackend,
    create_integration_queue,
)
from apps.integrations.core.registry import IntegrationRegistry, registry
from apps.integrations.core.state_store import get_last_cursor, update_cursor
from apps.integrations.models import CanonicalTaskRecord, IntegrationConnection

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    provider: str
    connection_id: str
    project_id: str
    tasks_processed: int
    events_published: int
    cursor: dict[str, Any]
    incremental: bool
    synced_at: str = field(default_factory=lambda: timezone.now().isoformat())
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "connection_id": self.connection_id,
            "project_id": self.project_id,
            "tasks_processed": self.tasks_processed,
            "events_published": self.events_published,
            "cursor": self.cursor,
            "incremental": self.incremental,
            "synced_at": self.synced_at,
            "details": self.details,
        }


def _snapshot_to_cursor(snapshot) -> IngestionCursor:
    return IngestionCursor(
        provider=snapshot.provider,
        connection_id=snapshot.connection_id,
        cursor=snapshot.last_sync_cursor,
        updated_at=snapshot.last_sync_time,
    )


class IngestionEngine:
    """
    Incremental ingestion orchestrator.

    Loads cursor via state_store, delegates delta fetch to the provider adapter,
    persists canonical tasks, publishes events to the Queue, and advances the cursor.
    """

    def __init__(
        self,
        integration_registry: IntegrationRegistry | None = None,
        queue: IntegrationQueueBackend | None = None,
    ) -> None:
        self._registry = integration_registry or registry
        self._queue = queue or create_integration_queue()

    def run(self, provider: str, connection_id: str) -> IngestionResult:
        connection = self._load_connection(connection_id, provider)
        adapter = self._registry.get(provider)

        snapshot = get_last_cursor(provider, connection_id)
        cursor_before = dict(snapshot.last_sync_cursor)
        state = _snapshot_to_cursor(snapshot)

        logger.info(
            "Starting incremental ingestion provider=%s connection_id=%s cursor=%s",
            provider,
            connection_id,
            cursor_before,
        )

        fetch_result = adapter.fetch_incremental(state, connection)
        tasks = adapter.map(fetch_result.payload, connection)
        saved_count = self._persist_tasks(connection, tasks)
        events_published = self._publish_events(
            provider=provider,
            connection=connection,
            tasks=tasks,
            fetch_result=fetch_result,
            cursor_before=cursor_before,
            saved_count=saved_count,
        )

        sync_time = timezone.now()
        update_cursor(provider, connection_id, fetch_result.cursor, sync_time=sync_time)
        connection.mark_synced()

        extra_details = getattr(adapter, "last_sync_details", None) or {}
        result = IngestionResult(
            provider=provider,
            connection_id=str(connection.pk),
            project_id=connection.project_id,
            tasks_processed=saved_count,
            events_published=events_published,
            cursor=fetch_result.cursor,
            incremental=bool(cursor_before.get("since")),
            synced_at=sync_time.isoformat(),
            details={
                **(extra_details if isinstance(extra_details, dict) else {}),
                "fetched_count": fetch_result.fetched_count,
                "complete": fetch_result.complete,
            },
        )

        emit_sync_completed(
            SyncCompletedEvent(
                provider=provider,
                connection_id=str(connection.pk),
                project_id=connection.project_id,
                tasks_synced=saved_count,
                synced_at=sync_time,
                details=result.details,
            )
        )

        logger.info(
            "Ingestion completed provider=%s connection_id=%s tasks=%d events=%d",
            provider,
            connection_id,
            saved_count,
            events_published,
        )
        return result

    def _load_connection(self, connection_id: str, provider: str) -> IntegrationConnection:
        try:
            return IntegrationConnection.objects.get(pk=connection_id, provider=provider)
        except IntegrationConnection.DoesNotExist as exc:
            raise ConnectionNotFoundError(connection_id) from exc

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

    def _publish_events(
        self,
        *,
        provider: str,
        connection: IntegrationConnection,
        tasks: list[CanonicalTask],
        fetch_result,
        cursor_before: dict[str, Any],
        saved_count: int,
    ) -> int:
        published = 0

        self._queue.publish(
            provider,
            IntegrationEvent(
                event_type="ingestion.started",
                provider=provider,
                connection_id=str(connection.pk),
                payload={
                    "project_id": connection.project_id,
                    "cursor_before": cursor_before,
                },
            ),
        )
        published += 1

        for task in tasks:
            self._queue.publish(
                provider,
                IntegrationEvent(
                    event_type="task.upserted",
                    provider=provider,
                    connection_id=str(connection.pk),
                    payload=task.as_dict(),
                ),
            )
            published += 1

        self._queue.publish(
            provider,
            IntegrationEvent(
                event_type="ingestion.completed",
                provider=provider,
                connection_id=str(connection.pk),
                payload={
                    "project_id": connection.project_id,
                    "tasks_processed": saved_count,
                    "cursor_after": fetch_result.cursor,
                    "fetched_count": fetch_result.fetched_count,
                },
            ),
        )
        published += 1

        return published
