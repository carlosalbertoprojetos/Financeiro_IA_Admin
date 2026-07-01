"""POCL — Pilot Operational Control Loop tests."""

from __future__ import annotations

import os
from unittest import mock

from rest_framework.test import APIClient
from django.test import TestCase
from django.utils import timezone

from apps.intelligence.models import (
    ActionImpactFollowUp,
    BusinessValueRecordModel,
    DecisionFeedbackRecord,
    PilotConfig,
    ReportAuditLog,
)
from apps.intelligence.services.decision_layer.models import DecisionObject
from apps.intelligence.services.decision_layer.queue.manager import enqueue_decision
from apps.intelligence.services.pilot.config import PilotConfigurationError, activate_pilot, ensure_human_in_loop, get_active_pilot
from apps.intelligence.services.pilot.evaluation import compute_pilot_metrics
from apps.intelligence.services.pilot.feedback import capture_rejection, record_decision_feedback
from apps.intelligence.services.pilot.impact_tracker import measure_followup, schedule_impact_followups
from apps.intelligence.services.pilot.report_generator import generate_executive_daily_report
from integrations.trello.models import Board


class PilotConfigTests(TestCase):
    def setUp(self) -> None:
        self.board = Board.objects.create(trello_id="board_pocl", name="POCL Board")

    @mock.patch.dict(os.environ, {"DAL_AUTO_EXECUTION": "false"})
    def test_activate_pilot(self) -> None:
        pilot = activate_pilot(board_id="board_pocl", team_name="Ops Alpha", duration_days=7)
        self.assertEqual(pilot.status, PilotConfig.Status.ACTIVE)
        self.assertEqual(get_active_pilot(board_id="board_pocl").id, pilot.id)
        self.assertTrue(pilot.config_json["real_mode"])

    @mock.patch.dict(os.environ, {"DAL_AUTO_EXECUTION": "false"})
    def test_activate_requires_existing_board(self) -> None:
        with self.assertRaises(PilotConfigurationError):
            activate_pilot(board_id="missing_board", team_name="Ops Alpha", duration_days=7)

    @mock.patch.dict(os.environ, {"DAL_AUTO_EXECUTION": "false"})
    def test_activate_requires_five_to_ten_days(self) -> None:
        with self.assertRaises(PilotConfigurationError):
            activate_pilot(board_id="board_pocl", team_name="Ops Alpha", duration_days=4)
        with self.assertRaises(PilotConfigurationError):
            activate_pilot(board_id="board_pocl", team_name="Ops Alpha", duration_days=11)

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

    def test_missing_card_state_skips_followup_without_inferred_impact(self) -> None:
        followup = ActionImpactFollowUp.objects.create(
            decision_id="dec_missing",
            action_type="ESCALATE_TASK",
            board_id="board_pocl",
            card_id="missing_card",
            window_hours=24,
            scheduled_at=timezone.now(),
            baseline_json={"observed": True, "risk_score": 80},
        )

        result = measure_followup(followup.id)

        followup.refresh_from_db()
        self.assertEqual(result["status"], "SKIPPED")
        self.assertEqual(followup.status, ActionImpactFollowUp.Status.SKIPPED)
        self.assertFalse(followup.impact_json["observed"])


class PilotMetricsTests(TestCase):
    def test_metrics_empty_board(self) -> None:
        metrics = compute_pilot_metrics(board_id="empty_board")
        self.assertEqual(metrics["suggestions_total"], 0)
        self.assertEqual(metrics["acceptance_rate_pct"], 0.0)


class PilotDashboardTests(TestCase):
    def test_dashboard_exposes_existing_pilot_data(self) -> None:
        decision = DecisionObject.create(
            insight="Risco de atraso em card critico",
            board_id="board_dash",
            priority="HIGH",
            recommended_actions=[{"action_type": "ESCALATE_TASK", "execution_mode": "MANUAL"}],
        )
        record = enqueue_decision(decision.to_dict())
        record_decision_feedback(
            decision_id=record.decision_id,
            disposition=DecisionFeedbackRecord.Disposition.ACCEPTED,
            operator="manager1",
        )
        ReportAuditLog.objects.create(
            board_id="board_dash",
            report_type="EXECUTIVO",
            export_format="pdf",
            matched_cards=4,
            result_summary={"report_quality_score": 82, "decision_value_score": 91},
        )
        BusinessValueRecordModel.objects.create(
            source_id="value_1",
            source_type="decision",
            value_type="avoided_loss",
            board_id="board_dash",
            realized_benefit=120,
            avoided_loss=500,
        )

        response = APIClient().get("/api/pilot/dashboard/?board_id=board_dash")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["usage"]["reports_generated"], 1)
        self.assertEqual(data["decisions"]["suggested"], 1)
        self.assertEqual(data["decisions"]["accepted"], 1)
        self.assertEqual(data["risks"]["detected"], 1)
        self.assertEqual(data["impact"]["avoided_loss"], 500)
        self.assertEqual(data["quality"]["latest_decision_value_score"], 91)
        self.assertFalse(data["operating_mode"]["destructive_actions_allowed"])


class ReportGeneratorTests(TestCase):
    @mock.patch.dict(os.environ, {"DAL_AUTO_EXECUTION": "false"})
    def test_generate_daily_report(self) -> None:
        Board.objects.create(trello_id="board_report", name="Report Board")
        pilot = activate_pilot(board_id="board_report", team_name="Team B")
        path = generate_executive_daily_report(board_id="board_report", pilot=pilot)
        self.assertTrue(path.endswith("executive_daily_report.md"))
