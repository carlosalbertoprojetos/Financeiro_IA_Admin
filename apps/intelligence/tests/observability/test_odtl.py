"""ODTL observability tests."""

from __future__ import annotations

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.intelligence.models import DecisionTraceRecord
from apps.intelligence.services.observability.lineage.metrics_lineage import build_metrics_lineage
from apps.intelligence.services.observability.lineage.query_lineage import build_query_lineage
from apps.intelligence.services.observability.storage import load_trace
from apps.intelligence.services.observability.trace.collector import TraceCollector, compute_query_id
from apps.intelligence.services.query_engine.runner import execute_eql_query
from apps.intelligence.tests.test_report_query import ReportQueryTestMixin


class TraceModelTests(TestCase):
    def test_query_id_reproducibility(self) -> None:
        q = "REPORT:\nTYPE = EXECUTIVE\nLIMIT:\n10"
        id1 = compute_query_id(q, "board1")
        id2 = compute_query_id(q, "board1")
        id3 = compute_query_id(q, "board2")
        self.assertEqual(id1, id2)
        self.assertNotEqual(id1, id3)

    def test_collector_records_steps(self) -> None:
        c = TraceCollector(query_text="test", board_id="b1")
        c.start_step("parse", "eql")
        c.end_step("parse", "eql", ok=True)
        self.assertEqual(len(c.trace.steps), 1)


class LineageTests(TestCase):
    def test_query_lineage(self) -> None:
        lineage = build_query_lineage(
            query_raw="REPORT:\nTYPE = EXECUTIVE",
            ast={"type": "EXECUTIVE", "limit": 100},
            optimized_plan={"scan": {"source": "timeline_events"}, "early_limit": True},
        )
        self.assertIn("eql_original", lineage)
        self.assertIn("execution_path", lineage["execution_path"] if False else lineage)
        self.assertTrue(lineage.get("execution_path"))

    def test_metrics_lineage(self) -> None:
        output = {
            "metrics": {"risk_score": {"avg": 55}},
            "business_metrics": {"incident_rate": {"value": 10}},
            "cards": [{"card_id": "c1", "risk_score": 70}],
        }
        lineage = build_metrics_lineage(output)
        metrics = {l["metric"] for l in lineage}
        self.assertIn("RISK_SCORE", metrics)


class TraceCompletenessTests(ReportQueryTestMixin, TestCase):
    def test_every_query_has_trace_id(self) -> None:
        query = """
REPORT:
TYPE = EXECUTIVE
FILTER:
PERIOD = LAST_30_DAYS
LIMIT:
100
"""
        result = execute_eql_query(query, board_id="rq_board", use_cache=False)
        self.assertIn("trace_id", result)
        self.assertIn("query_id", result)
        self.assertTrue(DecisionTraceRecord.objects.filter(trace_id=result["trace_id"]).exists())

    def test_trace_persisted_and_loadable(self) -> None:
        query = "REPORT:\nTYPE = EXECUTIVE\nFILTER:\nPERIOD = LAST_7_DAYS\nLIMIT:\n10"
        result = execute_eql_query(query, board_id="rq_board", use_cache=False)
        loaded = load_trace(result["trace_id"])
        assert loaded is not None
        self.assertEqual(loaded["trace_id"], result["trace_id"])
        self.assertTrue(len(loaded["steps"]) > 0)


class TraceAPITests(ReportQueryTestMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()
        self.query = "REPORT:\nTYPE = EXECUTIVE\nFILTER:\nPERIOD = LAST_7_DAYS\nLIMIT:\n10"
        self.result = execute_eql_query(self.query, board_id="rq_board", use_cache=False)

    def test_trace_detail_api(self) -> None:
        r = self.client.get(f"/api/traces/{self.result['trace_id']}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["trace_id"], self.result["trace_id"])

    def test_trace_by_query_api(self) -> None:
        r = self.client.get(f"/api/traces/query/{self.result['query_id']}/")
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(r.data["count"], 1)

    def test_insights_api(self) -> None:
        r = self.client.get("/api/traces/insights/")
        self.assertEqual(r.status_code, 200)

    def test_dashboard_api(self) -> None:
        r = self.client.get("/api/traces/dashboard/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("total_traces", r.data)


class DebugModeTests(ReportQueryTestMixin, TestCase):
    @override_settings()
    def test_debug_mode_includes_full_trace(self) -> None:
        import os
        os.environ["EOR_DEBUG_MODE"] = "true"
        try:
            from apps.intelligence.services.observability.config import is_debug_mode
            self.assertTrue(is_debug_mode())
            result = execute_eql_query(
                "REPORT:\nTYPE = EXECUTIVE\nFILTER:\nPERIOD = LAST_7_DAYS\nLIMIT:\n10",
                board_id="rq_board",
                use_cache=False,
            )
            self.assertIn("decision_trace", result)
            self.assertIn("metrics_lineage", result)
        finally:
            os.environ.pop("EOR_DEBUG_MODE", None)
