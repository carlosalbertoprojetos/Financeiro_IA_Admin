"""BVE — Business Value Engine tests."""

from __future__ import annotations

import os
from unittest import mock

from django.test import TestCase
from rest_framework.test import APIClient

from apps.intelligence.models import BusinessValueRecordModel
from apps.intelligence.services.business_value.attribution.engine import aggregate_by_dimension
from apps.intelligence.services.business_value.config import (
    action_cost_brl,
    base_impact_brl,
    hourly_rate_brl,
    hours_per_workday,
)
from apps.intelligence.services.business_value.cost_engine.calculator import (
    compute_blocking_cost,
    compute_delay_cost,
    compute_operational_costs,
    compute_rework_cost,
    compute_sla_breach_cost,
    compute_waiting_cost,
)
from apps.intelligence.services.business_value.pipeline import build_executive_value_dashboard, record_action_value
from apps.intelligence.services.business_value.productivity.engine import compute_productivity_value
from apps.intelligence.services.business_value.risk_value.engine import compute_avoided_loss, compute_expected_loss
from apps.intelligence.services.business_value.roi.engine import compute_action_roi
from apps.intelligence.services.business_value.trends.engine import compute_value_trends


def _seed_value(
    *,
    action_type: str = "ESCALATE_TASK",
    avoided: float = 5000,
    cost: float = 200,
    roi: float = 2400,
    category: str = "FINANCEIRO",
    team: str = "Ops",
    project: str = "Projeto A",
) -> BusinessValueRecordModel:
    return BusinessValueRecordModel.objects.create(
        source_id=f"src_{action_type}_{avoided}",
        source_type="action_execution",
        value_type="ACTION_ROI",
        estimated_cost=cost,
        estimated_benefit=avoided,
        realized_benefit=avoided * 0.8,
        avoided_loss=avoided,
        confidence_score=0.85,
        board_id="board1",
        action_type=action_type,
        category=category,
        team=team,
        project=project,
        roi_pct=roi,
        audit_json={"formula": "test"},
    )


class CostEngineTests(TestCase):
    def test_delay_cost(self) -> None:
        result = compute_delay_cost(days_overdue=5, assignees=2)
        self.assertGreater(result["estimated_cost"], 0)
        self.assertIn("confidence_score", result)

    def test_delay_cost_zero_days_lower_confidence(self) -> None:
        result = compute_delay_cost(days_overdue=0, assignees=1)
        self.assertEqual(result["confidence_score"], 0.5)
        self.assertEqual(result["estimated_cost"], 0)

    def test_rework_cost(self) -> None:
        result = compute_rework_cost(rework_events=3, hours_per_event=1.5)
        self.assertGreater(result["estimated_cost"], 0)
        self.assertEqual(result["confidence_score"], 0.8)

    def test_rework_cost_zero_events(self) -> None:
        result = compute_rework_cost(rework_events=0)
        self.assertEqual(result["confidence_score"], 0.3)

    def test_blocking_cost(self) -> None:
        result = compute_blocking_cost(blocked_hours=4, blocked_members=2)
        self.assertGreater(result["estimated_cost"], 0)

    def test_waiting_cost(self) -> None:
        result = compute_waiting_cost(wait_hours=6)
        self.assertGreater(result["estimated_cost"], 0)

    def test_sla_breach_cost(self) -> None:
        result = compute_sla_breach_cost(breach_probability=80, impact_brl=20000)
        self.assertEqual(result["estimated_cost"], 16000.0)

    def test_sla_breach_clamps_probability(self) -> None:
        result = compute_sla_breach_cost(breach_probability=150, impact_brl=1000)
        self.assertEqual(result["estimated_cost"], 1000.0)

    def test_operational_costs_from_card_state(self) -> None:
        costs = compute_operational_costs(
            card_state={"days_overdue": 3, "risk_score": 70, "assignee_count": 1},
            impact_brl=14000,
        )
        self.assertTrue(len(costs) >= 2)

    def test_operational_costs_all_types(self) -> None:
        costs = compute_operational_costs(
            card_state={
                "days_overdue": 2,
                "rework_events": 1,
                "blocked_hours": 3,
                "wait_hours": 5,
                "risk_score": 50,
            },
            impact_brl=10000,
        )
        types = {c["value_type"] for c in costs}
        self.assertIn("DELAY_COST", types)
        self.assertIn("REWORK_COST", types)
        self.assertIn("BLOCKING_COST", types)
        self.assertIn("WAITING_COST", types)
        self.assertIn("SLA_BREACH_COST", types)


class ConfigTests(TestCase):
    @mock.patch.dict(os.environ, {"BVE_HOURLY_RATE_BRL": "200"})
    def test_hourly_rate_env_override(self) -> None:
        self.assertEqual(hourly_rate_brl(), 200.0)

    @mock.patch.dict(os.environ, {"BVE_HOURLY_RATE_BRL": "bad"})
    def test_hourly_rate_invalid_fallback(self) -> None:
        self.assertEqual(hourly_rate_brl(), 150.0)

    @mock.patch.dict(os.environ, {"BVE_BASE_IMPACT_BRL": "25000"})
    def test_base_impact_env_override(self) -> None:
        self.assertEqual(base_impact_brl(), 25000.0)

    @mock.patch.dict(os.environ, {"BVE_HOURS_PER_WORKDAY": "6"})
    def test_hours_per_workday_override(self) -> None:
        self.assertEqual(hours_per_workday(), 6.0)

    @mock.patch.dict(os.environ, {"BVE_ACTION_COST_ESCALATE_TASK": "999"})
    def test_action_cost_env_override(self) -> None:
        self.assertEqual(action_cost_brl("ESCALATE_TASK"), 999.0)

    @mock.patch.dict(os.environ, {"BVE_ACTION_COST_ESCALATE_TASK": "x"})
    def test_action_cost_invalid_env_uses_default(self) -> None:
        self.assertEqual(action_cost_brl("ESCALATE_TASK"), 200.0)

    def test_action_cost_unknown_type_default(self) -> None:
        self.assertEqual(action_cost_brl("CUSTOM_ACTION"), 100.0)


class RiskValueEngineTests(TestCase):
    def test_expected_loss(self) -> None:
        result = compute_expected_loss(risk_score=90, impact_brl=20000)
        self.assertEqual(result["probability_pct"], 90.0)
        self.assertEqual(result["expected_loss"], 18000.0)

    def test_avoided_loss(self) -> None:
        result = compute_avoided_loss(risk_before=85, risk_after=40, impact_brl=17000)
        self.assertGreater(result["avoided_loss"], 0)


class ProductivityEngineTests(TestCase):
    def test_hours_saved(self) -> None:
        result = compute_productivity_value(risk_before=80, risk_after=40)
        self.assertGreater(result["hours_saved"], 0)
        self.assertGreater(result["estimated_benefit"], 0)


class RoiEngineTests(TestCase):
    def test_escalate_roi(self) -> None:
        result = compute_action_roi(action_type="ESCALATE_TASK", avoided_loss=5000, action_cost=200)
        self.assertEqual(result["action_cost"], 200)
        self.assertGreater(result["roi_pct"], 2000)

    def test_low_impact_roi(self) -> None:
        result = compute_action_roi(action_type="REASSIGN_OWNER", avoided_loss=100, action_cost=150)
        self.assertLess(result["roi_pct"], 0)


class RecordValuePipelineTests(TestCase):
    def test_record_action_value(self) -> None:
        record = record_action_value(
            decision_id="dec_v1",
            action_type="ESCALATE_TASK",
            before={"risk_score": 85, "sla_breach_probability": 85},
            after={"risk_score": 40, "sla_breach_probability": 40},
            board_id="board1",
            category="FINANCEIRO",
        )
        assert record is not None
        self.assertEqual(BusinessValueRecordModel.objects.count(), 1)
        self.assertGreater(record.avoided_loss, 0)
        self.assertGreater(record.roi_pct, 0)
        self.assertGreater(record.confidence_score, 0)


class AttributionTests(TestCase):
    def setUp(self) -> None:
        _seed_value(action_type="ESCALATE_TASK", team="Alpha")
        _seed_value(action_type="ESCALATE_TASK", avoided=3000, team="Alpha")
        _seed_value(action_type="REASSIGN_OWNER", avoided=200, roi=30, team="Beta")

    def test_aggregate_by_action(self) -> None:
        rows = aggregate_by_dimension("action", board_id="board1", days=90)
        self.assertGreaterEqual(len(rows), 2)
        escalate = next(r for r in rows if r["key"] == "ESCALATE_TASK")
        self.assertEqual(escalate["avoided_loss"], 8000)

    def test_aggregate_by_team(self) -> None:
        rows = aggregate_by_dimension("team", board_id="board1", days=90)
        alpha = next(r for r in rows if r["key"] == "Alpha")
        self.assertEqual(alpha["avoided_loss"], 8000)


class TrendsTests(TestCase):
    def test_value_trends(self) -> None:
        _seed_value()
        trends = compute_value_trends(board_id="board1")
        self.assertIn("monthly", trends)
        self.assertIn("quarterly", trends)
        self.assertIn("annual", trends)


class DashboardTests(TestCase):
    def setUp(self) -> None:
        for _ in range(3):
            _seed_value(avoided=16000)

    def test_executive_dashboard(self) -> None:
        dash = build_executive_value_dashboard(board_id="board1", days=90)
        self.assertEqual(dash["summary"]["records"], 3)
        self.assertGreater(dash["summary"]["losses_avoided_brl"], 0)
        self.assertTrue(len(dash["narratives"]) >= 1)


class ValueApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        _seed_value()

    def test_overview(self) -> None:
        r = self.client.get("/api/value/")
        self.assertEqual(r.status_code, 200)

    def test_dashboard(self) -> None:
        r = self.client.get("/api/value/dashboard/?board_id=board1")
        self.assertEqual(r.status_code, 200)
        self.assertIn("summary", r.data)

    def test_actions(self) -> None:
        r = self.client.get("/api/value/actions/?board_id=board1")
        self.assertEqual(r.status_code, 200)
        self.assertIn("actions", r.data)

    def test_teams(self) -> None:
        r = self.client.get("/api/value/teams/")
        self.assertEqual(r.status_code, 200)

    def test_projects(self) -> None:
        r = self.client.get("/api/value/projects/")
        self.assertEqual(r.status_code, 200)

    def test_trends(self) -> None:
        r = self.client.get("/api/value/trends/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("monthly", r.data)
