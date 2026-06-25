"""Additional QCL pipeline coverage tests."""

from __future__ import annotations

from django.core.cache import cache
from django.test import TestCase

from apps.intelligence.models import ReportQueryExecutionTrace
from apps.intelligence.services.eql.errors import QueryGuardRejectedError, QueryTimeoutError
from apps.intelligence.services.eql.parser import parse_eql
from apps.intelligence.services.eql.validator import validate_eql
from apps.intelligence.services.query_engine.compiler.compiler import compile_ast
from apps.intelligence.services.query_engine.compiler.plan import OptimizedQueryPlan, ScanSpec
from apps.intelligence.services.query_engine.cost_estimator.estimator import estimate_cost
from apps.intelligence.services.query_engine.executor import compute_actual_cost, execute_optimized_plan
from apps.intelligence.services.query_engine.optimizer.optimizer import optimize_plan
from apps.intelligence.services.query_engine.runner import execute_eql_query
from apps.intelligence.tests.test_report_query import ReportQueryTestMixin


class QCLPipelineTests(ReportQueryTestMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        cache.clear()

    def test_guard_rejects_missing_period(self) -> None:
        query = """
REPORT:
TYPE = EXECUTIVE
FILTER:
LABELS = Financeiro
LIMIT:
100
"""
        with self.assertRaises(QueryGuardRejectedError):
            execute_eql_query(query, board_id="rq_board", use_cache=False)

    def test_guard_rejection_traced(self) -> None:
        query = "REPORT:\nTYPE = EXECUTIVE\nFILTER:\nMEMBERS = Carlos\nLIMIT:\n100"
        with self.assertRaises(QueryGuardRejectedError):
            execute_eql_query(query, board_id="rq_board", use_cache=False)
        trace = ReportQueryExecutionTrace.objects.filter(rejected_by_guard=True).first()
        self.assertIsNotNone(trace)

    def test_optimizer_enriched_source_without_period(self) -> None:
        q = validate_eql(parse_eql("REPORT:\nTYPE = EXECUTIVE\nFILTER:\nTITLE_PREFIX = AQUI\nLIMIT:\n100", board_id="b1"))
        optimized = optimize_plan(compile_ast(q))
        self.assertIn(optimized.scan.source, ("enriched_context", "cards"))

    def test_compute_actual_cost(self) -> None:
        plan = OptimizedQueryPlan(
            report_type="EXECUTIVE",
            board_id="b1",
            scan=ScanSpec(source="cards"),
            grouping=["LABELS"],
            limit=100,
        )
        cost = compute_actual_cost(200, 5000, plan)
        self.assertGreater(cost, 0)
        self.assertLessEqual(cost, 100)

    def test_execute_optimized_plan_directly(self) -> None:
        ast = validate_eql(
            parse_eql(
                "REPORT:\nTYPE = EXECUTIVE\nFILTER:\nPERIOD = LAST_30_DAYS\nLIMIT:\n100",
                board_id="rq_board",
            )
        ).to_dict()
        plan = optimize_plan(compile_ast(ast))
        result = execute_optimized_plan(plan, ast_dict=ast)
        self.assertIn("summary", result)
        self.assertIn("execution_plan", result)

    def test_cost_estimate_medium_risk(self) -> None:
        q = validate_eql(
            parse_eql(
                "REPORT:\nTYPE = EXECUTIVE\n"
                "FILTER:\nPERIOD = LAST_90_DAYS\n"
                "LABELS = A\nMEMBERS = B\nSTATUS = ATRASADO\n"
                "GROUP_BY:\nLABELS\nLIMIT:\n100",
                board_id="b1",
            )
        )
        cost = estimate_cost(optimize_plan(compile_ast(q)))
        self.assertIn(cost.risk_level, ("LOW", "MEDIUM", "HIGH"))
