"""Additional EQL coverage tests."""

from __future__ import annotations

from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from apps.intelligence.models import ReportQueryLog, TimelineEvent
from apps.intelligence.services.eql.errors import InvalidFieldError
from apps.intelligence.services.query_engine.aggregation import (
    apply_risk_score_filter,
    ast_to_payload,
    build_standard_output,
    fetch_timeline_summary,
)
from apps.intelligence.services.query_engine.runner import execute_eql_query
from apps.intelligence.tests.test_report_query import ReportQueryTestMixin


class EQLAggregationTests(ReportQueryTestMixin, TestCase):
    def test_apply_risk_score_operators(self) -> None:
        spec = {"op": "<=", "value": 100}
        filtered = apply_risk_score_filter([self.card_aqui], spec)
        self.assertEqual(len(filtered), 1)

        spec_gt = {"op": ">", "value": 999}
        self.assertEqual(apply_risk_score_filter([self.card_aqui], spec_gt), [])

        spec_eq = {"op": "=", "value": 0}
        self.assertIsInstance(apply_risk_score_filter([self.card_aqui], spec_eq), list)

    def test_fetch_timeline_summary(self) -> None:
        TimelineEvent.objects.create(
            board=self.board,
            card=self.card_aqui,
            event_type="CARD_MOVED",
            event_timestamp=timezone.now(),
            actor="Carlos",
        )
        events = fetch_timeline_summary("rq_board", limit=5)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "CARD_MOVED")

    def test_ast_to_payload_period_and_status(self) -> None:
        payload = ast_to_payload(
            {
                "type": "EXECUTIVE",
                "board_id": "rq_board",
                "filters": {
                    "period": {"preset": "LAST_7_DAYS"},
                    "status": {"values": ["atrasado"], "operator": "OR"},
                },
                "metrics": ["LEAD_TIME"],
                "group_by": ["STATUS"],
                "sort": [{"field": "LEAD_TIME", "order": "ASC"}],
                "limit": 25,
            }
        )
        self.assertEqual(payload.board_id, "rq_board")
        self.assertEqual(payload.limit, 25)
        self.assertEqual(payload.status, ["atrasado"])

    def test_build_standard_output_recommendations(self) -> None:
        output = build_standard_output(
            query_ast={"type": "EXECUTIVE", "board_id": "rq_board", "limit": 10},
            cards=[self.card_aqui],
            card_rows=[{"risk_score": 80, "sla": "Atrasado"}],
            metrics_summary={"sla": {"compliance_pct": 50}},
            grouped={},
            processing_ms=10,
        )
        self.assertIn("summary", output)
        self.assertTrue(output["recommendations"])

    def test_limit_exceeds_validator_max(self) -> None:
        huge_limit = """
REPORT:
TYPE = EXECUTIVE
LIMIT:
2000
"""
        with self.assertRaises(InvalidFieldError):
            execute_eql_query(huge_limit, board_id="rq_board", use_cache=False)

    def test_runner_logs_error_on_invalid_field(self) -> None:
        before = ReportQueryLog.objects.count()
        with self.assertRaises(InvalidFieldError):
            execute_eql_query(
                "REPORT:\nTYPE = EXECUTIVE\nMETRICS:\nBOGUS\nLIMIT:\n10",
                board_id="rq_board",
                use_cache=False,
            )
        self.assertGreater(ReportQueryLog.objects.count(), before)
