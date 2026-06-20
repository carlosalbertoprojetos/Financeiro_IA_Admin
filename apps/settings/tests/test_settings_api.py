from django.test import TestCase
from rest_framework.test import APIClient

from apps.settings.models import WorkspaceConfig
from apps.settings.services import build_settings_overview, update_openai, update_workspace


class SettingsServicesTests(TestCase):
    def test_workspace_update_persists(self):
        update_workspace(workspace_name="Acme Ops")
        config = WorkspaceConfig.load()
        self.assertEqual(config.workspace_name, "Acme Ops")

    def test_openai_update_masks_in_overview(self):
        update_openai(api_key="sk-test-key-1234", model="gpt-4o-mini")
        overview = build_settings_overview()
        openai = overview["sections"]["openai"]
        self.assertTrue(openai["configured"])
        self.assertTrue(openai["api_key_masked"].endswith("1234"))


class SettingsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_overview_empty(self):
        response = self.client.get("/api/v1/settings/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "active")
        self.assertIn("workspace", data["sections"])

    def test_patch_workspace(self):
        response = self.client.patch(
            "/api/v1/settings/workspace/",
            {"workspace_name": "Meu Workspace"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["workspace_name"], "Meu Workspace")

    def test_patch_openai(self):
        response = self.client.patch(
            "/api/v1/settings/openai/",
            {"api_key": "sk-abc", "model": "gpt-4o"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["model"], "gpt-4o")

    def test_trello_post_requires_credentials(self):
        response = self.client.post("/api/v1/settings/trello/", {}, format="json")
        self.assertEqual(response.status_code, 400)
