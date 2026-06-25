"""Tests for report DSL parser and advanced query options."""

from django.test import TestCase

from apps.intelligence.services.report_query.domain.dsl_parser import parse_report_dsl
from apps.intelligence.services.report_query.domain.filters import ReportQueryPayload


USER_DSL = """
REPORT:
TYPE = EXECUTIVE

FILTER:
PERIOD = LAST_30_DAYS
LABELS = Financeiro AND Jurídico
MEMBERS = Carlos
TITLE_PREFIX = [AQUI]
STATUS = (ATRASADO OR BLOQUEADO)

METRICS:
LEAD_TIME, CYCLE_TIME, RISK_SCORE, SLA

GROUP_BY:
LABELS, MEMBERS

SORT:
RISK_SCORE DESC

LIMIT:
100
"""


class DSLParserTests(TestCase):
    def test_parse_user_report(self) -> None:
        parsed = parse_report_dsl(USER_DSL)
        self.assertEqual(parsed["report_type"], "EXECUTIVO")
        self.assertEqual(parsed["period"], "last_30_days")
        self.assertEqual(parsed["labels"], ["Financeiro", "Jurídico"])
        self.assertEqual(parsed["label_operator"], "and")
        self.assertEqual(parsed["members"], ["Carlos"])
        self.assertEqual(parsed["title_prefix"], "AQUI")
        self.assertEqual(parsed["status"], ["atrasado", "bloqueado"])
        self.assertEqual(parsed["status_operator"], "or")
        self.assertIn("LEAD_TIME", parsed["metrics"])
        self.assertIn("LABELS", parsed["group_by"])
        self.assertEqual(parsed["sort_by"], "RISK_SCORE")
        self.assertEqual(parsed["sort_order"], "DESC")
        self.assertEqual(parsed["limit"], 100)

    def test_payload_from_parsed_dsl(self) -> None:
        parsed = parse_report_dsl(USER_DSL)
        parsed["board_id"] = "test_board"
        payload = ReportQueryPayload.from_dict(parsed)
        self.assertEqual(payload.title_prefix, "AQUI")
        self.assertEqual(len(payload.metrics), 4)
        self.assertEqual(payload.limit, 100)
