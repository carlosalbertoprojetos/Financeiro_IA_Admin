from __future__ import annotations

import logging
import threading
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from django.conf import settings
from django.utils import timezone

from apps.integrations.models import IngestionQueueEvent

logger = logging.getLogger(__name__)

EventHandler = Callable[["IntegrationEvent"], None]


@dataclass(frozen=True)
class IntegrationEvent:
    """Message published to the integration event queue."""

    event_type: str
    provider: str
    connection_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: timezone.now())

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "provider": self.provider,
            "connection_id": self.connection_id,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IntegrationEvent:
        created_raw = data.get("created_at")
        created_at = (
            datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
            if isinstance(created_raw, str)
            else timezone.now()
        )
        return cls(
            event_type=data["event_type"],
            provider=data["provider"],
            connection_id=data["connection_id"],
            payload=data.get("payload") or {},
            created_at=created_at,
        )


# Backward-compatible alias
IngestionEvent = IntegrationEvent


class IntegrationQueueBackend(ABC):
    """
    Abstract integration event queue.

    Backends: local sync, local DB, local background thread, Celery, Kafka.
    """

    @abstractmethod
    def publish(self, provider: str, event: IntegrationEvent) -> None:
        """Enqueue an event for the given provider."""

    @abstractmethod
    def consume(
        self,
        provider: str,
        *,
        handler: EventHandler | None = None,
        limit: int = 100,
    ) -> list[IntegrationEvent]:
        """Consume pending events for a provider, optionally invoking a handler."""


class InMemoryIntegrationQueue(IntegrationQueueBackend):
    """In-memory queue — useful for unit tests."""

    def __init__(self) -> None:
        self._events: dict[str, list[IntegrationEvent]] = defaultdict(list)
        self.handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def register_handler(self, provider: str, handler: EventHandler) -> None:
        self.handlers[provider].append(handler)

    def publish(self, provider: str, event: IntegrationEvent) -> None:
        self._events[provider].append(event)
        for handler in self.handlers.get(provider, []):
            handler(event)

    @property
    def events(self) -> list[IntegrationEvent]:
        """Flattened event list (test helper)."""
        return [event for provider_events in self._events.values() for event in provider_events]

    def consume(
        self,
        provider: str,
        *,
        handler: EventHandler | None = None,
        limit: int = 100,
    ) -> list[IntegrationEvent]:
        pending = self._events.get(provider, [])[:limit]
        self._events[provider] = self._events.get(provider, [])[len(pending) :]

        if handler:
            for event in pending:
                handler(event)
        return pending


class DatabaseIntegrationQueue(IntegrationQueueBackend):
    """Persists events to the database (default local backend)."""

    def publish(self, provider: str, event: IntegrationEvent) -> None:
        IngestionQueueEvent.objects.create(
            event_type=event.event_type,
            provider=provider,
            connection_id=event.connection_id,
            payload=event.payload,
            processed=False,
        )

    def consume(
        self,
        provider: str,
        *,
        handler: EventHandler | None = None,
        limit: int = 100,
    ) -> list[IntegrationEvent]:
        records = list(
            IngestionQueueEvent.objects.filter(provider=provider, processed=False).order_by(
                "created_at"
            )[:limit]
        )
        if not records:
            return []

        consumed: list[IntegrationEvent] = []
        for record in records:
            event = IntegrationEvent(
                event_type=record.event_type,
                provider=record.provider,
                connection_id=record.connection_id,
                payload=record.payload or {},
                created_at=record.created_at,
            )
            if handler:
                handler(event)
            consumed.append(event)

        IngestionQueueEvent.objects.filter(pk__in=[record.pk for record in records]).update(
            processed=True
        )
        return consumed


class LocalSyncQueue(DatabaseIntegrationQueue):
    """
    Synchronous local queue.

    Persists events and immediately invokes registered handlers on publish.
    """

    def __init__(self) -> None:
        super().__init__()
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def register_handler(self, provider: str, handler: EventHandler) -> None:
        self._handlers[provider].append(handler)

    def publish(self, provider: str, event: IntegrationEvent) -> None:
        super().publish(provider, event)
        for handler in self._handlers.get(provider, []):
            try:
                handler(event)
            except Exception:
                logger.exception(
                    "Local sync handler failed provider=%s event_type=%s",
                    provider,
                    event.event_type,
                )


class LocalBackgroundQueue(DatabaseIntegrationQueue):
    """
    Local queue with asynchronous handler dispatch via background threads.

    Suitable when Celery/Kafka are not configured.
    """

    def __init__(self) -> None:
        super().__init__()
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def register_handler(self, provider: str, handler: EventHandler) -> None:
        self._handlers[provider].append(handler)

    def publish(self, provider: str, event: IntegrationEvent) -> None:
        super().publish(provider, event)
        handlers = list(self._handlers.get(provider, []))
        if not handlers:
            return

        thread = threading.Thread(
            target=self._dispatch,
            args=(provider, event, handlers),
            daemon=True,
            name=f"integration-queue-{provider}",
        )
        thread.start()

    def _dispatch(
        self,
        provider: str,
        event: IntegrationEvent,
        handlers: list[EventHandler],
    ) -> None:
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                logger.exception(
                    "Background handler failed provider=%s event_type=%s",
                    provider,
                    event.event_type,
                )

        record = (
            IngestionQueueEvent.objects.filter(
                provider=provider,
                connection_id=event.connection_id,
                event_type=event.event_type,
                processed=False,
            )
            .order_by("-created_at")
            .first()
        )
        if record:
            record.processed = True
            record.save(update_fields=["processed", "updated_at"])


class CeleryIntegrationQueue(IntegrationQueueBackend):
    """
    Celery-backed queue.

    publish() enqueues a Celery task; workers process events asynchronously.
    consume() drains any unprocessed DB records (audit / fallback path).
    """

    def __init__(self) -> None:
        self._fallback = DatabaseIntegrationQueue()

    def publish(self, provider: str, event: IntegrationEvent) -> None:
        self._fallback.publish(provider, event)
        from apps.integrations.tasks import dispatch_integration_event

        dispatch_integration_event.delay(provider, event.as_dict())

    def consume(
        self,
        provider: str,
        *,
        handler: EventHandler | None = None,
        limit: int = 100,
    ) -> list[IntegrationEvent]:
        return self._fallback.consume(provider, handler=handler, limit=limit)


class KafkaIntegrationQueue(IntegrationQueueBackend):
    """
    Kafka-backed queue (placeholder).

    Replace with a real producer/consumer when Kafka is adopted.
    """

    def publish(self, provider: str, event: IntegrationEvent) -> None:
        raise NotImplementedError(
            "Kafka integration queue is not configured. "
            "Use INTEGRATION_QUEUE_BACKEND=local_db or celery."
        )

    def consume(
        self,
        provider: str,
        *,
        handler: EventHandler | None = None,
        limit: int = 100,
    ) -> list[IntegrationEvent]:
        raise NotImplementedError(
            "Kafka integration queue is not configured. "
            "Use INTEGRATION_QUEUE_BACKEND=local_db or celery."
        )


_BACKENDS: dict[str, type[IntegrationQueueBackend]] = {
    "local_sync": LocalSyncQueue,
    "local_db": DatabaseIntegrationQueue,
    "local_background": LocalBackgroundQueue,
    "celery": CeleryIntegrationQueue,
    "kafka": KafkaIntegrationQueue,
}


def create_integration_queue(
    backend: str | None = None,
) -> IntegrationQueueBackend:
    """Factory for integration queue backends."""
    resolved = (backend or getattr(settings, "INTEGRATION_QUEUE_BACKEND", "local_db")).lower()
    queue_cls = _BACKENDS.get(resolved)
    if queue_cls is None:
        raise ValueError(
            f"Unknown INTEGRATION_QUEUE_BACKEND: {resolved}. "
            f"Supported: {', '.join(sorted(_BACKENDS))}"
        )
    return queue_cls()


_default_queue: IntegrationQueueBackend | None = None


def get_integration_queue() -> IntegrationQueueBackend:
    """Return the process-wide default integration queue."""
    global _default_queue
    if _default_queue is None:
        _default_queue = create_integration_queue()
    return _default_queue


# Backward-compatible aliases
IngestionQueue = IntegrationQueueBackend
DatabaseIngestionQueue = DatabaseIntegrationQueue
InMemoryIngestionQueue = InMemoryIntegrationQueue


def publish(provider: str, event: IntegrationEvent) -> None:
    """Publish an event using the default queue."""
    get_integration_queue().publish(provider, event)


def consume(
    provider: str,
    *,
    handler: EventHandler | None = None,
    limit: int = 100,
) -> list[IntegrationEvent]:
    """Consume events using the default queue."""
    return get_integration_queue().consume(provider, handler=handler, limit=limit)
