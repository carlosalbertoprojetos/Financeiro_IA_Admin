"""EQL execution engine tests."""

from __future__ import annotations

from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.intelligence.models import ReportQueryExecutionTrace, ReportQueryLog
from apps.intelligence.services.eql.errors import InvalidFieldError, MissingBoardIdError
from apps.intelligence.services.query_engine.compiler.compiler import compile_ast
from apps.intelligence.services.query_engine.optimizer.optimizer import optimize_plan
from apps.intelligence.services.query_engine.runner import execute_eql_query
from apps.intelligence.tests.test_report_query import ReportQueryTestMixin


EQL_SAMPLE = """
REPORT:
TYPE = EXECUTIVE

FILTER:
PERIOD = LAST_30_DAYS
LABELS = Financeiro
MEMBERS = Carlos
STATUS = ATRASADO
TITLE_PREFIX = [AQUI]

METRICS:
LEAD_TIME, RISK_SCORE

GROUP_BY:
LABELS

SORT:
RISK_SCORE DESC

LIMIT:
100
"""


class EQLExecutionTests(ReportQueryTestMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        cache.clear()

    def test_execute_combined_filters(self) -> None:
        result = execute_eql_query(EQL_SAMPLE, board_id="rq_board", use_cache=False)
        self.assertIn("summary", result)
        self.assertIn("metrics", result)
        self.assertIn("grouped_data", result)
        self.assertEqual(result["summary"]["board_id"], "rq_board")

    def test_execute_includes_plan_metadata(self) -> None:
        result = execute_eql_query(EQL_SAMPLE, board_id="rq_board", use_cache=False)
        self.assertIn("query_plan", result)
        self.assertIn("optimized_plan", result)
        self.assertIn("cost_estimate", result)
        self.assertIn("execution_plan", result)

    def test_grouping_and_sorting(self) -> None:
        query = """
REPORT:
TYPE = EXECUTIVE
FILTER:
PERIOD = LAST_30_DAYS
TITLE_PREFIX = AQUI
METRICS:
RISK_SCORE
GROUP_BY:
LABELS
SORT:
RISK_SCORE DESC
LIMIT:
10
"""
        result = execute_eql_query(query, board_id="rq_board", use_cache=False)
        self.assertIn("by_labels", result["grouped_data"])

    def test_query_plan_pushdown(self) -> None:
        from apps.intelligence.services.eql.parser import parse_eql
        from apps.intelligence.services.eql.validator import validate_eql

        parsed = validate_eql(parse_eql(EQL_SAMPLE, board_id="rq_board"))
        plan = compile_ast(parsed)
        optimized = optimize_plan(plan)
        self.assertEqual(plan.scan.source, "timeline_events")
        self.assertIn("period", optimized.filter_pushdown_order)

    def test_cache_hit(self) -> None:
        execute_eql_query(EQL_SAMPLE, board_id="rq_board", use_cache=True)
        result2 = execute_eql_query(EQL_SAMPLE, board_id="rq_board", use_cache=True)
        self.assertTrue(result2["summary"].get("cache_hit") or ReportQueryLog.objects.filter(cache_hit=True).exists())

    def test_execution_trace_created(self) -> None:
        execute_eql_query(EQL_SAMPLE, board_id="rq_board", use_cache=False)
        self.assertTrue(ReportQueryExecutionTrace.objects.filter(board_id="rq_board").exists())
        trace = ReportQueryExecutionTrace.objects.filter(board_id="rq_board").first()
        assert trace is not None
        self.assertIn("scan", trace.query_plan)
        self.assertIn("early_limit", trace.optimized_plan)

    def test_invalid_query_raises(self) -> None:
        with self.assertRaises(InvalidFieldError):
            execute_eql_query(
                "REPORT:\nTYPE = BAD\nLIMIT:\n10",
                board_id="rq_board",
                use_cache=False,
            )

    def test_performance_basic(self) -> None:
        import time

        start = time.perf_counter()
        execute_eql_query(EQL_SAMPLE, board_id="rq_board", use_cache=False)
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.assertLess(elapsed_ms, 30_000)


class EQLAPITests(ReportQueryTestMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()

    def test_eql_endpoint_get(self) -> None:
        response = self.client.get("/api/reports/eql/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("endpoint", response.data)

    def test_eql_endpoint_post(self) -> None:
        response = self.client.post(
            "/api/reports/eql/",
            {"board_id": "rq_board", "query": EQL_SAMPLE},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("summary", response.data)

    def test_eql_endpoint_missing_query(self) -> None:
        response = self.client.post("/api/reports/eql/", {"board_id": "rq_board"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_eql_endpoint_missing_board(self) -> None:
        response = self.client.post("/api/reports/eql/", {"query": "REPORT:\nTYPE = EXECUTIVE\nLIMIT:\n10"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_v1_eql_endpoint(self) -> None:
        response = self.client.post(
            "/api/v1/reports/eql/",
            {"board_id": "rq_board", "query": EQL_SAMPLE},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
