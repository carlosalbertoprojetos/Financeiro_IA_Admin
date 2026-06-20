import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="integrations.dispatch_integration_event")
def dispatch_integration_event(provider: str, event_data: dict) -> None:
    """Celery worker entrypoint — routes events to provider workers."""
    from apps.integrations.core.queue import IntegrationEvent

    event = IntegrationEvent.from_dict({**event_data, "provider": provider})
    logger.info(
        "Celery dispatch provider=%s type=%s connection=%s",
        provider,
        event.event_type,
        event.connection_id,
    )

    if provider == "trello":
        from apps.integrations.workers.trello_worker import TrelloWorker

        TrelloWorker().handle_event(event)
        return

    logger.warning("No worker registered for provider=%s", provider)


@shared_task(name="integrations.run_trello_worker")
def run_trello_worker_task(limit: int = 100) -> dict:
    """Drain the Trello integration queue."""
    from apps.integrations.workers.trello_worker import run_trello_worker

    return run_trello_worker(limit=limit)
