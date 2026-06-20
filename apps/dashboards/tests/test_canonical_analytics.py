from django.test import TestCase
from rest_framework.test import APIClient

from apps.dashboards.services.canonical_analytics import build_canonical_analytics
from apps.integrations.models import CanonicalTaskRecord, IntegrationConnection


class CanonicalAnalyticsTests(TestCase):
    def setUp(self):
        self.connection = IntegrationConnection.objects.create(
            provider="trello",
            name="Board Test",
            project_id="board123",
        )
        CanonicalTaskRecord.objects.create(
            connection=self.connection,
            source_provider="trello",
            source_id="c1",
            title="Task 1",
            status="Doing",
            project_id="board123",
            metadata={"closed": False},
        )

    def test_analytics_has_data(self):
        payload = build_canonical_analytics(project_id="board123", source_provider="trello")
        self.assertTrue(payload["has_data"])
        self.assertEqual(payload["summary"][0]["value"], "1")

    def test_analytics_api(self):
        client = APIClient()
        response = client.get("/api/v1/dashboards/analytics/?project_id=board123")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["has_data"])


class CanonicalReportApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.connection = IntegrationConnection.objects.create(
            provider="trello",
            name="Board Test",
            project_id="board123",
        )
        CanonicalTaskRecord.objects.create(
            connection=self.connection,
            source_provider="trello",
            source_id="c1",
            title="Task 1",
            status="Doing",
            project_id="board123",
            metadata={"closed": False},
        )

    def test_generate_pdf(self):
        response = self.client.post(
            "/api/v1/reports/executive/",
            {"board_id": "board123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_generate_pdf_without_data(self):
        CanonicalTaskRecord.objects.all().delete()
        response = self.client.post(
            "/api/v1/reports/executive/",
            {"board_id": "board123"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
