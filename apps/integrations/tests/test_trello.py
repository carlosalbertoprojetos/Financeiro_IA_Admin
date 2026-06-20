from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.integrations.core.canonical import CanonicalTask
from apps.integrations.models import IntegrationConnection
from apps.integrations.trello.mapper import map_trello_payload


SAMPLE_PAYLOAD = {
    "board": {
        "id": "b1",
        "name": "Sprint Board",
        "url": "https://trello.com/b/b1",
        "closed": False,
        "idOrganization": "org1",
    },
    "lists": [
        {"id": "l1", "name": "To Do", "closed": False},
        {"id": "l2", "name": "Done", "closed": False},
    ],
    "cards": [
        {
            "id": "c1",
            "name": "Card A",
            "idList": "l1",
            "due": "2026-06-20T12:00:00.000Z",
            "closed": False,
            "dueComplete": False,
            "labels": [{"id": "lb1", "name": "urgent", "color": "red"}],
            "url": "https://trello.com/c/c1",
        },
        {
            "id": "c2",
            "name": "Card B",
            "idList": "l2",
            "due": None,
            "closed": True,
            "dueComplete": False,
            "labels": [],
        },
    ],
    "workspace_id": "org1",
}


class TrelloMapperTests(TestCase):
    def test_map_board_to_project_and_list_to_status(self):
        tasks = map_trello_payload(SAMPLE_PAYLOAD, workspace_id="org1")

        self.assertEqual(len(tasks), 2)
        self.assertIsInstance(tasks[0], CanonicalTask)

        task_a = tasks[0]
        self.assertEqual(task_a.source_id, "c1")
        self.assertEqual(task_a.title, "Card A")
        self.assertEqual(task_a.status, "To Do")
        self.assertEqual(task_a.project_id, "b1")
        self.assertEqual(task_a.metadata["project_name"], "Sprint Board")
        self.assertEqual(task_a.metadata["workspace_id"], "org1")
        self.assertEqual(task_a.metadata["list_id"], "l1")

        task_b = tasks[1]
        self.assertEqual(task_b.status, "Done")
        self.assertTrue(task_b.metadata["closed"])


class TrelloAdapterTests(TestCase):
    @patch("apps.integrations.trello.adapter.TrelloClient")
    def test_sync_fetches_and_maps_real_shape(self, mock_client_cls):
        from apps.integrations.trello.adapter import TrelloAdapter

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.get_board.return_value = SAMPLE_PAYLOAD["board"]
        mock_client.get_lists.return_value = SAMPLE_PAYLOAD["lists"]
        mock_client.get_cards.return_value = SAMPLE_PAYLOAD["cards"]

        connection = IntegrationConnection.objects.create(
            provider="trello",
            project_id="b1",
            workspace_id="org1",
            credentials={"api_key": "k", "api_token": "t"},
        )

        adapter = TrelloAdapter()
        tasks = adapter.sync(connection)

        self.assertEqual(len(tasks), 2)
        self.assertEqual(adapter.last_sync_details["board_id"], "b1")
        self.assertEqual(adapter.last_sync_details["tasks_mapped"], 2)
        mock_client.get_board.assert_called()
        mock_client.get_lists.assert_called_with("b1")
        mock_client.get_cards.assert_called_with("b1")


class TrelloConnectViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("apps.integrations.trello.views.TrelloClient")
    def test_connect_creates_connection(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.api_key = "key"
        mock_client.api_token = "token"
        mock_client.get_member.return_value = {
            "id": "m1",
            "username": "dev",
            "fullName": "Developer",
        }
        mock_client.get_board.return_value = {
            "id": "b1",
            "name": "Board",
            "url": "https://trello.com/b/b1",
            "idOrganization": "org1",
            "closed": False,
        }
        mock_client.get_workspaces.return_value = [
            {"id": "org1", "name": "org", "displayName": "My Workspace", "url": ""},
        ]

        response = self.client.post(
            "/api/v1/integrations/trello/connect/",
            {
                "api_key": "key",
                "api_token": "token",
                "board_id": "b1",
                "workspace_id": "org1",
            },
            format="json",
        )

        self.assertIn(response.status_code, (200, 201))
        self.assertEqual(IntegrationConnection.objects.count(), 1)
        connection = IntegrationConnection.objects.get()
        self.assertEqual(connection.project_id, "b1")
        self.assertEqual(connection.workspace_id, "org1")
        self.assertEqual(connection.credentials["member_username"], "dev")

    @patch("apps.integrations.trello.adapter.TrelloClient")
    def test_sync_endpoint_runs_engine(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.get_board.return_value = SAMPLE_PAYLOAD["board"]
        mock_client.get_lists.return_value = SAMPLE_PAYLOAD["lists"]
        mock_client.get_cards.return_value = SAMPLE_PAYLOAD["cards"]

        connection = IntegrationConnection.objects.create(
            provider="trello",
            project_id="b1",
            workspace_id="org1",
            credentials={"api_key": "k", "api_token": "t"},
        )

        response = self.client.post(
            f"/api/v1/integrations/trello/connections/{connection.pk}/sync/",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["tasks_synced"], 2)
