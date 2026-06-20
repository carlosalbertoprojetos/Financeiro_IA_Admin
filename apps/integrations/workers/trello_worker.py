from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from django.db import transaction

from apps.integrations.core.exceptions import ConnectionNotFoundError
from apps.integrations.core.queue import IntegrationEvent, IntegrationQueueBackend, create_integration_queue
from apps.integrations.models import IntegrationConnection
from apps.integrations.services.analytics_sync import refresh_connection_analytics
from apps.integrations.services.task_persistence import canonical_task_from_payload, upsert_canonical_task
from apps.integrations.trello.mapper import map_trello_payload

logger = logging.getLogger(__name__)

PROVIDER = "trello"


@dataclass
class TrelloWorkerResult:
    events_processed: int = 0
    tasks_upserted: int = 0
    tasks_created: int = 0
    analytics_refreshed: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "events_processed": self.events_processed,
            "tasks_upserted": self.tasks_upserted,
            "tasks_created": self.tasks_created,
            "analytics_refreshed": self.analytics_refreshed,
            "skipped": self.skipped,
            "errors": self.errors,
        }


class TrelloWorker:
    """
    Consumes Trello integration queue events.

    - task.upserted → persist canonical task (idempotent upsert)
    - ingestion.completed → refresh analytics snapshot
    """

    def __init__(self, queue: IntegrationQueueBackend | None = None) -> None:
        self._queue = queue or create_integration_queue()
        self._connections_cache: dict[str, IntegrationConnection] = {}

    def run(self, *, limit: int = 100) -> TrelloWorkerResult:
        """Consume and process pending Trello queue events."""
        result = TrelloWorkerResult()

        def handler(event: IntegrationEvent) -> None:
            self._handle_event(event, result)

        self._queue.consume(PROVIDER, handler=handler, limit=limit)
        return result

    def handle_event(self, event: IntegrationEvent) -> None:
        """Process a single event (used by Celery dispatch)."""
        result = TrelloWorkerResult()
        self._handle_event(event, result)
        if result.errors:
            raise RuntimeError(result.errors[0])

    def _handle_event(self, event: IntegrationEvent, result: TrelloWorkerResult) -> None:
        if event.provider != PROVIDER:
            result.skipped += 1
            return

        result.events_processed += 1

        try:
            if event.event_type == "task.upserted":
                self._process_task_upserted(event, result)
            elif event.event_type == "ingestion.completed":
                self._process_ingestion_completed(event, result)
            else:
                result.skipped += 1
        except Exception as exc:
            logger.exception(
                "Trello worker failed event_type=%s connection=%s",
                event.event_type,
                event.connection_id,
            )
            result.errors.append(str(exc))

    @transaction.atomic
    def _process_task_upserted(self, event: IntegrationEvent, result: TrelloWorkerResult) -> None:
        connection = self._get_connection(event.connection_id)
        payload = event.payload

        if "source_provider" in payload and "source_id" in payload:
            task = canonical_task_from_payload(payload)
        else:
            task = self._map_raw_card_payload(payload, connection)

        _, created = upsert_canonical_task(connection, task)
        result.tasks_upserted += 1
        if created:
            result.tasks_created += 1

        logger.debug(
            "Trello worker upserted task provider=%s source_id=%s created=%s",
            task.source_provider,
            task.source_id,
            created,
        )

    def _process_ingestion_completed(self, event: IntegrationEvent, result: TrelloWorkerResult) -> None:
        connection = self._get_connection(event.connection_id)
        refresh_connection_analytics(connection)
        result.analytics_refreshed += 1
        logger.info(
            "Trello worker refreshed analytics connection_id=%s project_id=%s",
            event.connection_id,
            connection.project_id,
        )

    def _map_raw_card_payload(
        self,
        payload: dict[str, Any],
        connection: IntegrationConnection,
    ):
        """Support raw Trello fetch payloads when present on the event."""
        if "board" in payload and "cards" in payload:
            tasks = map_trello_payload(
                payload,
                workspace_id=connection.workspace_id,
            )
            if len(tasks) != 1:
                raise ValueError("Raw payload must contain exactly one card for task.upserted")
            return tasks[0]

        raise ValueError("Unsupported task.upserted payload shape")

    def _get_connection(self, connection_id: str) -> IntegrationConnection:
        if connection_id not in self._connections_cache:
            try:
                self._connections_cache[connection_id] = IntegrationConnection.objects.get(
                    pk=connection_id,
                    provider=PROVIDER,
                )
            except IntegrationConnection.DoesNotExist as exc:
                raise ConnectionNotFoundError(connection_id) from exc
        return self._connections_cache[connection_id]


def run_trello_worker(*, limit: int = 100) -> dict[str, Any]:
    """Entry point for management commands and periodic jobs."""
    return TrelloWorker().run(limit=limit).as_dict()
