from datetime import datetime, timezone

from django.test import SimpleTestCase

from analytics.engine.types import ActionRecord, CardRecord, StatusTransition
from dashboard.services.builders import (
    build_dashboard_bottlenecks,
    build_dashboard_efficiency,
    build_dashboard_overview,
    build_dashboard_productivity,
)


class DashboardBuildersTests(SimpleTestCase):
    def setUp(self):
        self.created = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
        self.started = datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc)
        self.completed = datetime(2026, 6, 5, 10, 0, tzinfo=timezone.utc)
        self.due = datetime(2026, 6, 4, 10, 0, tzinfo=timezone.utc)
        self.now = datetime(2026, 6, 10, 10, 0, tzinfo=timezone.utc)

        self.completed_card = CardRecord(
            id="card-1",
            title="Done card",
            status="Done",
            created_at=self.created,
            completed_at=self.completed,
            due_at=self.due,
            is_closed=True,
            assignee_ids=("member-1",),
            assignee_names=("Alice",),
            status_history=(
                StatusTransition(status="Backlog", effective_at=self.created, list_position=1.0),
                StatusTransition(status="In Progress", effective_at=self.started, list_position=2.0),
                StatusTransition(status="Done", effective_at=self.completed, list_position=3.0),
            ),
        )
        self.open_card = CardRecord(
            id="card-2",
            title="Open card",
            status="In Progress",
            created_at=self.created,
            due_at=self.due,
            status_history=(
                StatusTransition(status="Backlog", effective_at=self.created, list_position=1.0),
                StatusTransition(status="In Progress", effective_at=self.started, list_position=2.0),
            ),
        )
        self.cards = [self.completed_card, self.open_card]
        self.actions = [
            ActionRecord(
                id="action-1",
                action_type="updateCard",
                occurred_at=self.started,
                card_id="card-2",
                raw_json={
                    "data": {
                        "card": {"id": "card-2"},
                        "listBefore": {"name": "Review", "pos": 3.0},
                        "listAfter": {"name": "In Progress", "pos": 2.0},
                    }
                },
            )
        ]

    def test_build_dashboard_overview(self):
        payload = build_dashboard_overview(
            self.cards, self.actions, board_id="board-1", reference_time=self.now
        )
        self.assertEqual(payload["endpoint"], "dashboard/overview")
        self.assertIn("health_score", payload)
        self.assertIn("status_distribution", payload)

    def test_build_dashboard_productivity(self):
        payload = build_dashboard_productivity(
            self.cards, self.actions, board_id="board-1", reference_time=self.now
        )
        self.assertEqual(payload["endpoint"], "dashboard/productivity")
        self.assertEqual(len(payload["team_output"]), 1)
        self.assertIn("productivity_score", payload)

    def test_build_dashboard_efficiency(self):
        payload = build_dashboard_efficiency(
            self.cards, self.actions, board_id="board-1", reference_time=self.now
        )
        self.assertEqual(payload["endpoint"], "dashboard/efficiency")
        self.assertIn("comparison", payload)
        self.assertIn("efficiency_score", payload)

    def test_build_dashboard_bottlenecks(self):
        payload = build_dashboard_bottlenecks(
            self.cards, self.actions, board_id="board-1", reference_time=self.now
        )
        self.assertEqual(payload["endpoint"], "dashboard/bottlenecks")
        self.assertIn("wip_by_status", payload)
        self.assertIn("bottleneck_statuses", payload)
