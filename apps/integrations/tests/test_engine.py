from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.integrations.core.adapter import BaseIntegrationAdapter
from apps.integrations.core.canonical import CanonicalTask
from apps.integrations.core.engine import SyncEngine
from apps.integrations.core.events import sync_completed
from apps.integrations.core.exceptions import ProviderNotRegisteredError, ProviderNotReadyError
from apps.integrations.core.registry import IntegrationRegistry
from apps.integrations.models import CanonicalTaskRecord, IntegrationConnection


class StubAdapter(BaseIntegrationAdapter):
    provider = "stub"

    def authenticate(self, connection: IntegrationConnection) -> None:
        pass

    def fetch(self, connection: IntegrationConnection):
        return {"items": [{"id": "1", "title": "Task A", "status": "open"}]}

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


class IntegrationRegistryTests(TestCase):
    def test_register_and_get(self):
        reg = IntegrationRegistry()
        reg.register(StubAdapter)
        adapter = reg.get("stub")
        self.assertIsInstance(adapter, StubAdapter)

    def test_unknown_provider_raises(self):
        reg = IntegrationRegistry()
        with self.assertRaises(ProviderNotRegisteredError):
            reg.get("unknown")


class SyncEngineTests(TestCase):
    def setUp(self):
        self.registry = IntegrationRegistry()
        self.registry.register(StubAdapter)
        self.engine = SyncEngine(integration_registry=self.registry)
        self.connection = IntegrationConnection.objects.create(
            name="Test",
            provider="stub",
            project_id="proj-1",
        )

    def test_run_persists_canonical_tasks(self):
        result = self.engine.run("stub", str(self.connection.pk))
        self.assertEqual(result.tasks_synced, 1)
        self.assertEqual(CanonicalTaskRecord.objects.count(), 1)
        record = CanonicalTaskRecord.objects.get()
        self.assertEqual(record.title, "Task A")
        self.assertEqual(record.source_provider, "stub")

    def test_run_emits_sync_completed_signal(self):
        received = []

        def handler(sender, **kwargs):
            received.append(kwargs)

        sync_completed.connect(handler, dispatch_uid="test-sync-completed")
        try:
            self.engine.run("stub", str(self.connection.pk))
        finally:
            sync_completed.disconnect(dispatch_uid="test-sync-completed")

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["provider"], "stub")
        self.assertEqual(received[0]["tasks_synced"], 1)


class BuiltInRegistryTests(TestCase):
    def test_builtin_providers_registered(self):
        from apps.integrations.core.registry import registry

        self.assertEqual(
            registry.list_providers(),
            [
                "asana",
                "azure_devops",
                "clickup",
                "github_projects",
                "jira",
                "monday",
                "notion",
                "planner",
                "trello",
            ],
        )

    def test_jira_not_ready(self):
        from apps.integrations.core.registry import registry

        connection = IntegrationConnection.objects.create(
            provider="jira",
            project_id="JIRA-1",
        )
        adapter = registry.get("jira")
        with self.assertRaises(ProviderNotReadyError):
            adapter.sync(connection)


class TrelloAdapterTests(TestCase):
    @patch("apps.integrations.trello.adapter.TrelloClient")
    def test_trello_sync_maps_cards(self, mock_client_cls):
        from apps.integrations.trello.adapter import TrelloAdapter

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.get_board.return_value = {"id": "b1", "name": "Board", "idOrganization": ""}
        mock_client.get_lists.return_value = [{"id": "l1", "name": "Doing"}]
        mock_client.get_cards.return_value = [
            {"id": "c1", "name": "Card 1", "idList": "l1", "due": None, "closed": False, "labels": []},
        ]

        connection = IntegrationConnection.objects.create(
            provider="trello",
            project_id="b1",
            credentials={"api_key": "k", "api_token": "t"},
        )

        adapter = TrelloAdapter()
        tasks = adapter.sync(connection)

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].title, "Card 1")
        self.assertEqual(tasks[0].status, "Doing")
