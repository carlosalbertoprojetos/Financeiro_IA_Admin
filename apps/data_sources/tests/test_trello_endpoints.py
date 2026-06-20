from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.integrations.core.credentials import decrypt_credentials, encrypt_credentials
from apps.integrations.models import IntegrationConnection


class CredentialEncryptionTests(TestCase):
    def test_encrypt_decrypt_roundtrip(self):
        raw = {"api_key": "key123", "api_token": "token456", "member_id": "m1"}
        encrypted = encrypt_credentials(raw)
        self.assertTrue(encrypted["_encrypted"])
        self.assertNotEqual(encrypted["api_key"], "key123")

        decrypted = decrypt_credentials(encrypted)
        self.assertEqual(decrypted["api_key"], "key123")
        self.assertEqual(decrypted["api_token"], "token456")
        self.assertEqual(decrypted["member_id"], "m1")


class DataSourceTrelloEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("apps.data_sources.trello_views.TrelloClient")
    def test_connect_validates_and_encrypts_credentials(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.api_key = "key"
        mock_client.api_token = "token"
        mock_client.get_member.return_value = {"id": "m1", "username": "dev"}

        response = self.client.post(
            "/api/v1/data-sources/trello/connect/",
            {"api_key": "key", "api_token": "token"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "connected")
        connection = IntegrationConnection.objects.get()
        stored = connection.credentials
        self.assertTrue(stored["_encrypted"])
        decrypted = decrypt_credentials(stored)
        self.assertEqual(decrypted["api_key"], "key")
        self.assertEqual(decrypted["api_token"], "token")

    @patch("apps.integrations.trello.adapter.TrelloClient")
    def test_sync_runs_integration_engine(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.get_board.return_value = {
            "id": "b1",
            "name": "Board",
            "idOrganization": "org1",
        }
        mock_client.get_lists.return_value = [{"id": "l1", "name": "Doing"}]
        mock_client.get_cards.return_value = [
            {"id": "c1", "name": "Task", "idList": "l1", "labels": []},
        ]

        encrypted = encrypt_credentials(
            {"api_key": "k", "api_token": "t", "member_id": "m1", "member_username": "dev"}
        )
        IntegrationConnection.objects.create(
            provider="trello",
            project_id="b1",
            credentials=encrypted,
        )

        response = self.client.post(
            "/api/v1/data-sources/trello/sync/",
            {"board_id": "b1"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["tasks_synced"], 1)

    def test_status_disconnected_when_no_connection(self):
        response = self.client.get("/api/v1/data-sources/trello/status/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "disconnected")

    @patch("apps.data_sources.trello_views.TrelloClient")
    def test_status_connected(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.api_key = "key"
        mock_client.api_token = "token"
        mock_client.get_member.return_value = {"id": "m1", "username": "dev"}

        self.client.post(
            "/api/v1/data-sources/trello/connect/",
            {"api_key": "key", "api_token": "token"},
            format="json",
        )

        response = self.client.get("/api/v1/data-sources/trello/status/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "connected")
        self.assertTrue(response.data["credentials_configured"])
        self.assertEqual(response.data["member"]["username"], "dev")
