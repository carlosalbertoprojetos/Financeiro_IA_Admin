from django.test import TestCase

from apps.integrations.core.queue import (
    DatabaseIntegrationQueue,
    InMemoryIntegrationQueue,
    IntegrationEvent,
    LocalBackgroundQueue,
    LocalSyncQueue,
    consume,
    create_integration_queue,
    publish,
)
from apps.integrations.models import IngestionQueueEvent


class IntegrationQueueTests(TestCase):
    def test_in_memory_publish_and_consume(self):
        queue = InMemoryIntegrationQueue()
        event = IntegrationEvent(
            event_type="task.upserted",
            provider="trello",
            connection_id="1",
            payload={"title": "Task"},
        )

        queue.publish("trello", event)
        consumed = queue.consume("trello")

        self.assertEqual(len(consumed), 1)
        self.assertEqual(consumed[0].event_type, "task.upserted")
        self.assertEqual(queue.consume("trello"), [])

    def test_database_queue_marks_processed(self):
        queue = DatabaseIntegrationQueue()
        queue.publish(
            "trello",
            IntegrationEvent(
                event_type="ingestion.completed",
                provider="trello",
                connection_id="1",
                payload={},
            ),
        )

        self.assertEqual(IngestionQueueEvent.objects.filter(processed=False).count(), 1)
        consumed = queue.consume("trello")
        self.assertEqual(len(consumed), 1)
        self.assertEqual(IngestionQueueEvent.objects.filter(processed=True).count(), 1)

    def test_local_sync_invokes_handler(self):
        queue = LocalSyncQueue()
        received: list[str] = []
        queue.register_handler("trello", lambda event: received.append(event.event_type))

        queue.publish(
            "trello",
            IntegrationEvent(
                event_type="ingestion.started",
                provider="trello",
                connection_id="1",
            ),
        )

        self.assertEqual(received, ["ingestion.started"])

    def test_local_background_invokes_handler(self):
        import time

        queue = LocalBackgroundQueue()
        received: list[str] = []
        queue.register_handler("jira", lambda event: received.append(event.event_type))

        queue.publish(
            "jira",
            IntegrationEvent(
                event_type="ingestion.completed",
                provider="jira",
                connection_id="2",
            ),
        )

        deadline = time.time() + 2
        while time.time() < deadline and not received:
            time.sleep(0.05)

        self.assertEqual(received, ["ingestion.completed"])

    def test_module_helpers_use_default_queue(self):
        publish(
            "clickup",
            IntegrationEvent(
                event_type="ingestion.started",
                provider="clickup",
                connection_id="3",
            ),
        )
        consumed = consume("clickup")
        self.assertEqual(len(consumed), 1)

    def test_factory_unknown_backend_raises(self):
        with self.assertRaises(ValueError):
            create_integration_queue("unknown")

    def test_kafka_backend_not_implemented(self):
        queue = create_integration_queue("kafka")
        with self.assertRaises(NotImplementedError):
            queue.publish(
                "trello",
                IntegrationEvent(
                    event_type="test",
                    provider="trello",
                    connection_id="1",
                ),
            )
