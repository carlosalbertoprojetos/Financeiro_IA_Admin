from datetime import datetime, timezone

from django.test import SimpleTestCase

from analytics.engine.metrics import (
    aging,
    compute_all,
    cycle_time,
    delay_rate,
    lead_time,
    rework_rate,
    throughput,
)
from analytics.engine.types import ActionRecord, CardRecord, StatusTransition


class AnalyticsEngineTests(SimpleTestCase):
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

    def test_lead_time(self):
        result = lead_time(self.cards)
        self.assertEqual(result["metric"], "lead_time")
        self.assertEqual(result["summary"]["count"], 1)
        self.assertEqual(result["items"][0]["card_id"], "card-1")
        self.assertEqual(result["items"][0]["lead_time_hours"], 96.0)

    def test_cycle_time(self):
        result = cycle_time(self.cards)
        self.assertEqual(result["summary"]["count"], 1)
        self.assertEqual(result["items"][0]["cycle_time_hours"], 72.0)

    def test_throughput(self):
        result = throughput(self.cards, period="day")
        self.assertEqual(result["summary"]["total_completed"], 1)
        self.assertEqual(result["series"][0]["count"], 1)

    def test_aging(self):
        result = aging([self.open_card], reference_time=self.now)
        self.assertEqual(result["summary"]["count"], 1)
        self.assertEqual(result["items"][0]["aging_hours"], 192.0)

    def test_delay_rate(self):
        result = delay_rate(self.cards, reference_time=self.now)
        self.assertEqual(result["summary"]["total_with_due_date"], 2)
        self.assertEqual(result["summary"]["delayed"], 2)
        self.assertEqual(result["summary"]["delay_rate"], 1.0)

    def test_rework_rate(self):
        actions = [
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
        result = rework_rate(actions, cards=self.cards)
        self.assertEqual(result["summary"]["rework_events"], 1)
        self.assertEqual(result["summary"]["cards_with_rework"], 1)
        self.assertEqual(result["summary"]["rework_rate"], 0.5)

    def test_compute_all(self):
        actions = [
            ActionRecord(
                id="action-1",
                action_type="commentCard",
                occurred_at=self.started,
                card_id="card-1",
                raw_json={"data": {"card": {"id": "card-1"}}},
            )
        ]
        result = compute_all(self.cards, actions, reference_time=self.now)
        self.assertIn("metrics", result)
        self.assertEqual(
            set(result["metrics"].keys()),
            {
                "lead_time",
                "cycle_time",
                "throughput",
                "aging",
                "delay_rate",
                "rework_rate",
            },
        )
