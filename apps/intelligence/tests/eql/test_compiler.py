"""QCL compiler tests."""

from __future__ import annotations

from django.test import TestCase

from apps.intelligence.services.eql.parser import parse_eql
from apps.intelligence.services.eql.validator import validate_eql
from apps.intelligence.services.query_engine.compiler.compiler import compile_ast


SAMPLE = """
REPORT:
TYPE = EXECUTIVE
FILTER:
PERIOD = LAST_30_DAYS
LABELS = Financeiro AND Jurídico
MEMBERS = Carlos
STATUS = ATRASADO
TITLE_PREFIX = [AQUI]
RISK_SCORE >= 70
METRICS:
LEAD_TIME, RISK_SCORE
GROUP_BY:
LABELS, MEMBERS
SORT:
RISK_SCORE DESC
LIMIT:
100
"""


class CompilerTests(TestCase):
    def test_ast_to_plan(self) -> None:
        validated = validate_eql(parse_eql(SAMPLE, board_id="b1"))
        plan = compile_ast(validated)
        self.assertEqual(plan.report_type, "EXECUTIVE")
        self.assertEqual(plan.board_id, "b1")
        self.assertEqual(plan.scan.source, "timeline_events")
        self.assertIn("cards", plan.scan.secondary_sources)
        self.assertEqual(plan.limit, 100)
        self.assertTrue(any(f.field == "period" for f in plan.filters))
        self.assertEqual(plan.grouping, ["LABELS", "MEMBERS"])
        self.assertEqual(len(plan.pre_aggregations), 2)

    def test_source_selection_cards_only(self) -> None:
        q = validate_eql(parse_eql("REPORT:\nTYPE = EXECUTIVE\nLIMIT:\n50", board_id="b1"))
        plan = compile_ast(q)
        self.assertEqual(plan.scan.source, "cards")

    def test_parallel_strategy(self) -> None:
        validated = validate_eql(parse_eql(SAMPLE, board_id="b1"))
        plan = compile_ast(validated)
        self.assertEqual(plan.execution_strategy, "PARALLEL")

    def test_plan_to_dict(self) -> None:
        validated = validate_eql(parse_eql(SAMPLE, board_id="b1"))
        plan = compile_ast(validated)
        d = plan.to_dict()
        self.assertIn("scan", d)
        self.assertIn("filters", d)
        self.assertIn("execution_strategy", d)
