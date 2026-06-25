"""EQL parser tests."""

from __future__ import annotations

from django.test import TestCase

from apps.intelligence.services.eql.errors import SyntaxError as EQLSyntaxError
from apps.intelligence.services.eql.parser import parse_eql


SAMPLE_QUERY = """
REPORT:
TYPE = EXECUTIVE

FILTER:
PERIOD = LAST_30_DAYS
LABELS = Financeiro AND Jurídico
MEMBERS = Carlos OR João
STATUS = (ATRASADO OR BLOQUEADO)
TITLE_PREFIX = [AQUI]
RISK_SCORE >= 70

METRICS:
LEAD_TIME, CYCLE_TIME, RISK_SCORE, SLA

GROUP_BY:
LABELS, MEMBERS

SORT:
RISK_SCORE DESC
LEAD_TIME ASC

LIMIT:
100
"""


class EQLParserTests(TestCase):
    def test_parse_valid_query(self) -> None:
        query = parse_eql(SAMPLE_QUERY, board_id="board1")
        self.assertEqual(query.type, "EXECUTIVE")
        self.assertEqual(query.board_id, "board1")
        self.assertEqual(query.limit, 100)
        self.assertIn("period", query.filters)
        self.assertEqual(query.filters["period"]["preset"], "LAST_30_DAYS")
        self.assertEqual(query.filters["labels"]["operator"], "AND")
        self.assertEqual(query.filters["members"]["operator"], "OR")
        self.assertEqual(query.filters["status"]["values"], ["atrasado", "bloqueado"])
        self.assertEqual(query.filters["title_prefix"], "AQUI")
        self.assertEqual(query.filters["risk_score"]["op"], ">=")
        self.assertEqual(len(query.metrics), 4)
        self.assertEqual(query.group_by, ["LABELS", "MEMBERS"])
        self.assertEqual(len(query.sort), 2)

    def test_parse_custom_period(self) -> None:
        query = parse_eql(
            "REPORT:\nTYPE = OPERATIONAL\nFILTER:\nPERIOD = CUSTOM_RANGE FROM 01/01/2026 TO 31/03/2026\nLIMIT:\n50",
            board_id="b1",
        )
        self.assertEqual(query.type, "OPERATIONAL")
        self.assertEqual(query.filters["period"]["preset"], "CUSTOM")
        self.assertEqual(query.limit, 50)

    def test_parse_invalid_filter_line(self) -> None:
        with self.assertRaises(EQLSyntaxError):
            parse_eql("REPORT:\nTYPE = EXECUTIVE\nFILTER:\nUNKNOWN = x\nLIMIT:\n10", board_id="b1")

    def test_parse_status_simple(self) -> None:
        query = parse_eql("REPORT:\nTYPE = EXECUTIVE\nFILTER:\nSTATUS = ATRASADO\nLIMIT:\n10", board_id="b1")
        self.assertEqual(query.filters["status"]["values"], ["atrasado"])

    def test_parse_board_id_in_filter(self) -> None:
        query = parse_eql("REPORT:\nTYPE = EXECUTIVE\nFILTER:\nBOARD_ID = myboard\nLIMIT:\n10")
        self.assertEqual(query.board_id, "myboard")

    def test_parse_aliases(self) -> None:
        query = parse_eql("REPORT:\nTYPE = EXECUTIVO\nLIMIT:\n25", board_id="b1")
        self.assertEqual(query.type, "EXECUTIVE")
