from django.test import TestCase
from rest_framework.test import APIClient

from apps.dashboards.services.scope import resolve_canonical_scope
from apps.integrations.models import CanonicalTaskRecord, IntegrationConnection


class CanonicalScopeTests(TestCase):
    def setUp(self):
        self.connection = IntegrationConnection.objects.create(
            provider="trello",
            name="Board Test",
            project_id="board123",
        )
        for index in range(3):
            CanonicalTaskRecord.objects.create(
                connection=self.connection,
                source_provider="trello",
                source_id=f"c{index}",
                title=f"Task {index}",
                status="Doing",
                project_id="board123",
            )

    def test_connection_id_wins_over_wrong_board_id(self):
        scope = resolve_canonical_scope(
            connection_id=str(self.connection.pk),
            project_id="wrong-board",
        )
        self.assertEqual(scope.task_count(), 3)

    def test_report_with_connection_id_and_wrong_board(self):
        client = APIClient()
        response = client.post(
            "/api/v1/reports/executive/",
            {
                "connection_id": str(self.connection.pk),
                "board_id": "wrong-board",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_reports_overview_uses_connection(self):
        client = APIClient()
        response = client.get(
            f"/api/v1/reports/?connection_id={self.connection.pk}&board_id=wrong-board"
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["has_data"])
        self.assertEqual(body["tasks_count"], 3)
