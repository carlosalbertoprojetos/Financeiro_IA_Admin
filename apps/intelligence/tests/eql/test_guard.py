"""Query guard and cost estimator tests."""

from __future__ import annotations

from django.test import TestCase

from apps.intelligence.services.eql.errors import QueryCostRejectedError, QueryGuardRejectedError
from apps.intelligence.services.eql.parser import parse_eql
from apps.intelligence.services.eql.validator import validate_eql
from apps.intelligence.services.query_engine.compiler.compiler import compile_ast
from apps.intelligence.services.query_engine.compiler.plan import OptimizedQueryPlan, QueryPlan, ScanSpec
from apps.intelligence.services.query_engine.cost_estimator.estimator import estimate_cost
from apps.intelligence.services.query_engine.guard.guard import guard_query
from apps.intelligence.services.query_engine.optimizer.optimizer import optimize_plan


class CostEstimatorTests(TestCase):
    def test_low_cost_simple_query(self) -> None:
        q = validate_eql(
            parse_eql("REPORT:\nTYPE = EXECUTIVE\nFILTER:\nPERIOD = LAST_7_DAYS\nLIMIT:\n50", board_id="b1")
        )
        cost = estimate_cost(optimize_plan(compile_ast(q)))
        self.assertLess(cost.estimated_cost, 55)
        self.assertEqual(cost.recommendation, "ALLOW")
        self.assertEqual(cost.risk_level, "LOW")

    def test_high_cost_many_filters(self) -> None:
        q = validate_eql(
            parse_eql(
                "REPORT:\nTYPE = EXECUTIVE\n"
                "FILTER:\nPERIOD = LAST_90_DAYS\n"
                "LABELS = A AND B\nMEMBERS = C\nSTATUS = ATRASADO\n"
                "TITLE_PREFIX = X\nRISK_SCORE >= 50\n"
                "GROUP_BY:\nLABELS, MEMBERS, STATUS\n"
                "LIMIT:\n100",
                board_id="b1",
            )
        )
        cost = estimate_cost(optimize_plan(compile_ast(q)))
        self.assertGreater(cost.number_of_filters, 3)
        self.assertGreater(cost.grouping_complexity, 0)
        self.assertIn(cost.risk_level, ("LOW", "MEDIUM", "HIGH"))

    def test_cost_to_dict(self) -> None:
        q = validate_eql(parse_eql("REPORT:\nTYPE = EXECUTIVE\nFILTER:\nPERIOD = LAST_7_DAYS\nLIMIT:\n10", board_id="b1"))
        cost = estimate_cost(optimize_plan(compile_ast(q)))
        d = cost.to_dict()
        self.assertIn("estimated_cost", d)
        self.assertIn("recommendation", d)


class GuardTests(TestCase):
    def test_missing_temporal_scope(self) -> None:
        q = validate_eql(parse_eql("REPORT:\nTYPE = EXECUTIVE\nFILTER:\nLABELS = Financeiro\nLIMIT:\n100", board_id="b1"))
        plan = optimize_plan(compile_ast(q))
        cost = estimate_cost(plan)
        with self.assertRaises(QueryGuardRejectedError):
            guard_query(plan, cost)

    def test_group_by_without_limit(self) -> None:
        plan = OptimizedQueryPlan(
            report_type="EXECUTIVE",
            board_id="b1",
            scan=ScanSpec(source="cards"),
            grouping=["LABELS"],
            limit=600,
            filters=[],
        )
        cost = estimate_cost(plan)
        with self.assertRaises(QueryGuardRejectedError):
            guard_query(plan, cost)

    def test_reject_high_cost(self) -> None:
        plan = OptimizedQueryPlan(
            report_type="EXECUTIVE",
            board_id="b1",
            scan=ScanSpec(source="enriched_context", secondary_sources=["cards", "timeline_events"]),
            grouping=["LABELS", "MEMBERS", "STATUS"],
            limit=100,
            max_scan_rows=5000,
            filters=[],
        )
        from apps.intelligence.services.query_engine.cost_estimator.estimator import CostEstimate

        cost = CostEstimate(
            estimated_cost=90,
            risk_level="HIGH",
            recommendation="REJECT",
            estimated_rows=4000,
            number_of_filters=6,
            grouping_complexity=6,
            joins_required=3,
            source_type_cost=40,
        )
        with self.assertRaises(QueryCostRejectedError):
            guard_query(plan, cost)

    def test_allow_valid_query(self) -> None:
        q = validate_eql(
            parse_eql("REPORT:\nTYPE = EXECUTIVE\nFILTER:\nPERIOD = LAST_7_DAYS\nLIMIT:\n100", board_id="b1")
        )
        plan = optimize_plan(compile_ast(q))
        cost = estimate_cost(plan)
        guard_query(plan, cost)
