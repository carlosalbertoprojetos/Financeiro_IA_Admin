from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.integrations.models import CanonicalTaskRecord, IntegrationConnection


class CanonicalDashboardMetricsViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        connection = IntegrationConnection.objects.create(provider="trello", project_id="b1")
        now = timezone.now()
        CanonicalTaskRecord.objects.create(
            connection=connection,
            source_provider="trello",
            source_id="c1",
            title="Task",
            status="Doing",
            project_id="b1",
            due_date=now - timedelta(days=1),
        )

    def test_metrics_endpoint(self):
        response = self.client.get("/api/v1/dashboards/metrics/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["summary"]["total_tasks"], 1)
        self.assertIn("tasks_by_status", response.data)
        self.assertIn("trend_7d", response.data)
        self.assertEqual(len(response.data["trend_7d"]), 7)
