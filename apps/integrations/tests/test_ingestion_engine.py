from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from apps.integrations.core.adapter import BaseIntegrationAdapter, IncrementalFetchResult
from apps.integrations.core.canonical import CanonicalTask
from apps.integrations.core.exceptions import ProviderNotReadyError
from apps.integrations.core.ingestion_engine import IngestionEngine
from apps.integrations.core.ingestion_state import IngestionCursor
from apps.integrations.core.queue import InMemoryIntegrationQueue, IntegrationEvent
from apps.integrations.core.registry import IntegrationRegistry
from apps.integrations.core.state_store import get_last_cursor, update_cursor
from apps.integrations.models import (
    CanonicalTaskRecord,
    IngestionQueueEvent,
    IntegrationConnection,
    IntegrationState,
)


class IncrementalStubAdapter(BaseIntegrationAdapter):
    provider = "stub"

    def authenticate(self, connection: IntegrationConnection) -> None:
        pass

    def fetch(self, connection: IntegrationConnection):
        return {"items": [{"id": "1", "title": "A", "status": "open"}]}

    def map(self, raw_payload, connection: IntegrationConnection) -> list[CanonicalTask]:
        return [
            CanonicalTask(
                source_provider=self.provider,
                source_id=item["id"],
                title=item["title"],
                status=item["status"],
                project_id=connection.project_id,
            )
            for item in raw_payload["items"]
        ]

    def fetch_incremental(self, state: IngestionCursor, connection: IntegrationConnection):
        mode = "incremental" if state.get("since") else "initial"
        return IncrementalFetchResult(
            payload={"items": [{"id": "1", "title": "A", "status": "open"}]},
            cursor={"since": "2026-06-19T12:00:00+00:00", "mode": mode},
            fetched_count=1,
        )


class StateStoreTests(TestCase):
    def setUp(self):
        self.connection = IntegrationConnection.objects.create(
            provider="trello",
            project_id="b1",
        )

    def test_get_last_cursor_returns_empty_state(self):
        snapshot = get_last_cursor("trello", str(self.connection.pk))

        self.assertEqual(snapshot.provider, "trello")
        self.assertEqual(snapshot.connection_id, str(self.connection.pk))
        self.assertEqual(snapshot.last_sync_cursor, {})
        self.assertIsNone(snapshot.last_sync_time)

    def test_update_cursor_persists_state(self):
        sync_time = timezone.now()
        update_cursor(
            "trello",
            str(self.connection.pk),
            {"since": "2026-06-19T10:00:00+00:00", "mode": "initial"},
            sync_time=sync_time,
        )

        self.assertEqual(IntegrationState.objects.count(), 1)
        snapshot = get_last_cursor("trello", str(self.connection.pk))
        self.assertEqual(snapshot.last_sync_cursor["mode"], "initial")
        self.assertIsNotNone(snapshot.last_sync_time)


class IngestionEngineTests(TestCase):
    def setUp(self):
        self.registry = IntegrationRegistry()
        self.registry.register(IncrementalStubAdapter)
        self.queue = InMemoryIntegrationQueue()
        self.engine = IngestionEngine(
            integration_registry=self.registry,
            queue=self.queue,
        )
        self.connection = IntegrationConnection.objects.create(
            provider="stub",
            project_id="proj-1",
        )

    def test_run_persists_tasks_and_updates_cursor(self):
        result = self.engine.run("stub", str(self.connection.pk))

        self.assertEqual(result.tasks_processed, 1)
        self.assertEqual(CanonicalTaskRecord.objects.count(), 1)

        snapshot = get_last_cursor("stub", str(self.connection.pk))
        self.assertEqual(snapshot.last_sync_cursor["since"], "2026-06-19T12:00:00+00:00")
        self.assertIsNotNone(snapshot.last_sync_time)

    def test_run_publishes_queue_events(self):
        self.engine.run("stub", str(self.connection.pk))

        event_types = [event.event_type for event in self.queue.events]
        self.assertEqual(event_types[0], "ingestion.started")
        self.assertIn("task.upserted", event_types)
        self.assertEqual(event_types[-1], "ingestion.completed")

    def test_second_run_is_incremental(self):
        self.engine.run("stub", str(self.connection.pk))
        result = self.engine.run("stub", str(self.connection.pk))
        self.assertTrue(result.incremental)


class TrelloIncrementalAdapterTests(TestCase):
    @patch("apps.integrations.trello.adapter.TrelloClient")
    def test_fetch_incremental_filters_by_activity(self, mock_client_cls):
        from apps.integrations.trello.adapter import TrelloAdapter

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.get_board.return_value = {"id": "b1", "name": "Board", "idOrganization": ""}
        mock_client.get_lists.return_value = [{"id": "l1", "name": "Doing"}]
        mock_client.get_cards.return_value = [
            {
                "id": "c1",
                "name": "old",
                "idList": "l1",
                "dateLastActivity": "2026-06-01T10:00:00.000Z",
                "labels": [],
            },
            {
                "id": "c2",
                "name": "new",
                "idList": "l1",
                "dateLastActivity": "2026-06-19T10:00:00.000Z",
                "labels": [],
            },
        ]

        connection = IntegrationConnection.objects.create(
            provider="trello",
            project_id="b1",
            credentials={"api_key": "k", "api_token": "t"},
        )
        state = IngestionCursor(
            provider="trello",
            connection_id=str(connection.pk),
            cursor={
                "updated_since": "2026-06-18T00:00:00+00:00",
                "card_list_map": {"c1": "l1"},
            },
        )

        adapter = TrelloAdapter()
        result = adapter.fetch_incremental(state, connection)

        ids = {card["id"] for card in result.payload["cards"]}
        self.assertEqual(ids, {"c2"})
        self.assertEqual(result.cursor["mode"], "incremental")


class MultiProviderIngestionTests(TestCase):
    def test_jira_not_ready_on_incremental(self):
        from apps.integrations.core.registry import registry

        connection = IntegrationConnection.objects.create(provider="jira", project_id="J1")
        adapter = registry.get("jira")
        state = IngestionCursor(provider="jira", connection_id=str(connection.pk))

        with self.assertRaises(ProviderNotReadyError):
            adapter.fetch_incremental(state, connection)

    def test_clickup_not_ready_on_incremental(self):
        from apps.integrations.core.registry import registry

        connection = IntegrationConnection.objects.create(provider="clickup", project_id="C1")
        adapter = registry.get("clickup")
        state = IngestionCursor(provider="clickup", connection_id=str(connection.pk))

        with self.assertRaises(ProviderNotReadyError):
            adapter.fetch_incremental(state, connection)


class DatabaseQueueTests(TestCase):
    def test_database_queue_persists_events(self):
        from apps.integrations.core.queue import DatabaseIntegrationQueue

        queue = DatabaseIntegrationQueue()
        queue.publish(
            "trello",
            IntegrationEvent(
                event_type="ingestion.completed",
                provider="trello",
                connection_id="1",
                payload={"tasks_processed": 3},
            ),
        )

        self.assertEqual(IngestionQueueEvent.objects.count(), 1)
