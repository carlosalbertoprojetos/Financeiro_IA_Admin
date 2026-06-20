from django.test import TestCase
from django.core.cache import cache

from apps.integrations.core.queue import DatabaseIntegrationQueue, IntegrationEvent
from apps.integrations.models import CanonicalTaskRecord, IntegrationConnection
from apps.integrations.services.analytics_sync import analytics_cache_key, get_cached_analytics_summary
from apps.integrations.workers.trello_worker import TrelloWorker


class TrelloWorkerTests(TestCase):
    def setUp(self):
        cache.clear()
        self.connection = IntegrationConnection.objects.create(
            provider="trello",
            project_id="b1",
            name="Board",
        )
        self.queue = DatabaseIntegrationQueue()
        self.worker = TrelloWorker(queue=self.queue)

    def _task_event(self, source_id: str = "c1") -> IntegrationEvent:
        return IntegrationEvent(
            event_type="task.upserted",
            provider="trello",
            connection_id=str(self.connection.pk),
            payload={
                "source_provider": "trello",
                "source_id": source_id,
                "title": "Task A",
                "status": "Doing",
                "project_id": "b1",
                "due_date": None,
                "metadata": {"list_id": "l1"},
            },
        )

    def test_processes_task_upserted_idempotently(self):
        self.queue.publish("trello", self._task_event())
        self.queue.publish("trello", self._task_event())

        result = self.worker.run(limit=10)

        self.assertEqual(result.tasks_upserted, 2)
        self.assertEqual(result.tasks_created, 1)
        self.assertEqual(CanonicalTaskRecord.objects.count(), 1)

        record = CanonicalTaskRecord.objects.get()
        self.assertEqual(record.title, "Task A")
        self.assertEqual(record.status, "Doing")

    def test_ingestion_completed_refreshes_analytics_cache(self):
        CanonicalTaskRecord.objects.create(
            connection=self.connection,
            source_provider="trello",
            source_id="c1",
            title="Existing",
            status="Done",
            project_id="b1",
        )
        self.queue.publish(
            "trello",
            IntegrationEvent(
                event_type="ingestion.completed",
                provider="trello",
                connection_id=str(self.connection.pk),
                payload={"project_id": "b1", "tasks_processed": 1},
            ),
        )

        result = self.worker.run(limit=10)

        self.assertEqual(result.analytics_refreshed, 1)
        summary = get_cached_analytics_summary(provider="trello", project_id="b1")
        self.assertIsNotNone(summary)
        self.assertEqual(summary["total_tasks"], 1)
        self.connection.refresh_from_db()
        self.assertIsNotNone(self.connection.last_synced_at)

    def test_skips_non_trello_events(self):
        self.queue.publish(
            "jira",
            IntegrationEvent(
                event_type="task.upserted",
                provider="jira",
                connection_id="99",
                payload={},
            ),
        )
        worker = TrelloWorker(queue=self.queue)
        result = worker.run(limit=10)
        self.assertEqual(result.events_processed, 0)

    def test_handle_event_single_task(self):
        event = self._task_event(source_id="c99")
        self.worker.handle_event(event)
        self.assertTrue(
            CanonicalTaskRecord.objects.filter(source_id="c99").exists()
        )

    def test_analytics_cache_key(self):
        self.assertEqual(
            analytics_cache_key("trello", "b1"),
            "integrations:analytics:trello:b1",
        )
