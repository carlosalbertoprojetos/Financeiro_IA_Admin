"""QCL optimizer tests."""

from __future__ import annotations

from django.test import TestCase

from apps.intelligence.services.eql.parser import parse_eql
from apps.intelligence.services.eql.validator import validate_eql
from apps.intelligence.services.query_engine.compiler.compiler import compile_ast
from apps.intelligence.services.query_engine.optimizer.optimizer import optimize_plan


class OptimizerTests(TestCase):
    def test_filter_pushdown(self) -> None:
        q = validate_eql(
            parse_eql(
                "REPORT:\nTYPE = EXECUTIVE\nFILTER:\nPERIOD = LAST_7_DAYS\nLABELS = Financeiro\nLIMIT:\n100",
                board_id="b1",
            )
        )
        plan = compile_ast(q)
        optimized = optimize_plan(plan)
        self.assertIn("filter_pushdown:labels", optimized.optimization_notes)
        self.assertTrue(optimized.filters[0].pushdown or optimized.filter_pushdown_order)

    def test_source_selection_timeline(self) -> None:
        q = validate_eql(
            parse_eql(
                "REPORT:\nTYPE = EXECUTIVE\nFILTER:\nPERIOD = LAST_30_DAYS\nLIMIT:\n100",
                board_id="b1",
            )
        )
        optimized = optimize_plan(compile_ast(q))
        self.assertEqual(optimized.scan.source, "timeline_events")

    def test_early_limit(self) -> None:
        q = validate_eql(parse_eql("REPORT:\nTYPE = EXECUTIVE\nFILTER:\nPERIOD = LAST_7_DAYS\nLIMIT:\n50", board_id="b1"))
        optimized = optimize_plan(compile_ast(q))
        self.assertTrue(optimized.early_limit)
        self.assertIn("early_limit_applied", optimized.optimization_notes)

    def test_parallel_dimensions(self) -> None:
        q = validate_eql(
            parse_eql(
                "REPORT:\nTYPE = EXECUTIVE\n"
                "FILTER:\nPERIOD = LAST_30_DAYS\nLABELS = A\nMEMBERS = B\nSTATUS = ATRASADO\n"
                "LIMIT:\n100",
                board_id="b1",
            )
        )
        optimized = optimize_plan(compile_ast(q))
        self.assertEqual(optimized.execution_strategy, "PARALLEL")
        self.assertGreaterEqual(len(optimized.parallel_dimensions), 2)

    def test_enriched_context_source(self) -> None:
        q = validate_eql(
            parse_eql(
                "REPORT:\nTYPE = EXECUTIVE\nFILTER:\nLABELS = Financeiro\nPERIOD = LAST_7_DAYS\nLIMIT:\n100",
                board_id="b1",
            )
        )
        optimized = optimize_plan(compile_ast(q))
        self.assertIn(optimized.scan.source, ("timeline_events", "enriched_context"))
