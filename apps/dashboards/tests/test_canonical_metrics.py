from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.dashboards.services.canonical_metrics import build_canonical_dashboard
from apps.integrations.models import CanonicalTaskRecord, IntegrationConnection


class CanonicalDashboardMetricsTests(TestCase):
    def setUp(self):
        self.connection = IntegrationConnection.objects.create(
            provider="trello",
            project_id="b1",
            name="Board 1",
        )
        now = timezone.now()

        CanonicalTaskRecord.objects.create(
            connection=self.connection,
            source_provider="trello",
            source_id="c1",
            title="Open task",
            status="Doing",
            project_id="b1",
            due_date=now + timedelta(days=2),
        )
        CanonicalTaskRecord.objects.create(
            connection=self.connection,
            source_provider="trello",
            source_id="c2",
            title="Overdue task",
            status="Doing",
            project_id="b1",
            due_date=now - timedelta(days=1),
        )
        CanonicalTaskRecord.objects.create(
            connection=self.connection,
            source_provider="jira",
            source_id="J-1",
            title="Jira task",
            status="Done",
            project_id="PROJ",
        )

    def test_tasks_by_status(self):
        payload = build_canonical_dashboard()
        statuses = {row["status"]: row["count"] for row in payload["tasks_by_status"]}
        self.assertEqual(statuses["Doing"], 2)
        self.assertEqual(statuses["Done"], 1)

    def test_overdue_tasks(self):
        payload = build_canonical_dashboard()
        self.assertEqual(payload["overdue_tasks"]["count"], 1)
        self.assertEqual(payload["overdue_tasks"]["items"][0]["title"], "Overdue task")

    def test_by_source_provider(self):
        payload = build_canonical_dashboard()
        providers = {row["source_provider"]: row["count"] for row in payload["by_source_provider"]}
        self.assertEqual(providers["trello"], 2)
        self.assertEqual(providers["jira"], 1)

    def test_trend_7d_has_seven_points(self):
        payload = build_canonical_dashboard()
        self.assertEqual(len(payload["trend_7d"]), 7)

    def test_project_filter(self):
        payload = build_canonical_dashboard(project_id="b1")
        self.assertEqual(payload["summary"]["total_tasks"], 2)
