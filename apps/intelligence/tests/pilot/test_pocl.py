"""POCL — Pilot Operational Control Loop tests."""

from __future__ import annotations

import os
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from apps.intelligence.models import (
    ActionImpactFollowUp,
    DecisionFeedbackRecord,
    PilotConfig,
)
from apps.intelligence.services.decision_layer.models import DecisionObject
from apps.intelligence.services.decision_layer.queue.manager import enqueue_decision
from apps.intelligence.services.pilot.config import PilotConfigurationError, activate_pilot, ensure_human_in_loop, get_active_pilot
from apps.intelligence.services.pilot.evaluation import compute_pilot_metrics
from apps.intelligence.services.pilot.feedback import capture_rejection, record_decision_feedback
from apps.intelligence.services.pilot.impact_tracker import schedule_impact_followups
from apps.intelligence.services.pilot.report_generator import generate_executive_daily_report


class PilotConfigTests(TestCase):
    @mock.patch.dict(os.environ, {"DAL_AUTO_EXECUTION": "false"})
    def test_activate_pilot(self) -> None:
        pilot = activate_pilot(board_id="board_pocl", team_name="Ops Alpha", duration_days=7)
        self.assertEqual(pilot.status, PilotConfig.Status.ACTIVE)
        self.assertEqual(get_active_pilot(board_id="board_pocl").id, pilot.id)

    @mock.patch.dict(os.environ, {"DAL_AUTO_EXECUTION": "true"})
    def test_human_in_loop_required(self) -> None:
        with self.assertRaises(PilotConfigurationError):
            ensure_human_in_loop()


class FeedbackTests(TestCase):
    def setUp(self) -> None:
        decision = DecisionObject.create(
            insight="Escalate overdue task",
            board_id="board_pocl",
            recommended_actions=[{"action_type": "ESCALATE_TASK", "execution_mode": "SEMI_AUTOMATIC"}],
        )
        self.record = enqueue_decision(decision.to_dict())

    def test_record_accepted_feedback(self) -> None:
        fb = record_decision_feedback(
            decision_id=self.record.decision_id,
            disposition=DecisionFeedbackRecord.Disposition.ACCEPTED,
            operator="manager1",
        )
        self.assertEqual(fb.disposition, "ACCEPTED")

    def test_rejection_marks_decision_rejected(self) -> None:
        capture_rejection(
            decision_id=self.record.decision_id,
            operator="manager1",
            reason="not needed",
        )
        from apps.intelligence.services.decision_layer.queue.manager import load_decision
        loaded = load_decision(self.record.decision_id)
        self.assertEqual(loaded["status"], "REJECTED")


class ImpactTrackerTests(TestCase):
    def test_schedule_followups(self) -> None:
        followups = schedule_impact_followups(
            decision_id="dec_1",
            action_type="ESCALATE_TASK",
            board_id="board_pocl",
            card_id="card_1",
            baseline={"risk_score": 80},
        )
        self.assertEqual(len(followups), 3)
        windows = {f.window_hours for f in followups}
        self.assertEqual(windows, {24, 72, 168})


class PilotMetricsTests(TestCase):
    def test_metrics_empty_board(self) -> None:
        metrics = compute_pilot_metrics(board_id="empty_board")
        self.assertEqual(metrics["suggestions_total"], 0)
        self.assertEqual(metrics["acceptance_rate_pct"], 0.0)


class ReportGeneratorTests(TestCase):
    @mock.patch.dict(os.environ, {"DAL_AUTO_EXECUTION": "false"})
    def test_generate_daily_report(self) -> None:
        pilot = activate_pilot(board_id="board_report", team_name="Team B")
        path = generate_executive_daily_report(board_id="board_report", pilot=pilot)
        self.assertTrue(path.endswith("executive_daily_report.md"))
