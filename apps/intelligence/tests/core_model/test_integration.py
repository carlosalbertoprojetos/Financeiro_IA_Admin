"""CMGL integration tests."""

from __future__ import annotations

from django.core.cache import cache
from django.test import TestCase

from apps.intelligence.services.core_model.errors import CrossLayerValidationError
from apps.intelligence.services.eql.errors import InvalidFieldError
from apps.intelligence.services.query_engine.runner import execute_eql_query
from apps.intelligence.tests.test_report_query import ReportQueryTestMixin


class CMGLIntegrationTests(ReportQueryTestMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        cache.clear()

    def test_pipeline_includes_governance(self) -> None:
        query = """
REPORT:
TYPE = EXECUTIVE
FILTER:
PERIOD = LAST_30_DAYS
LIMIT:
100
"""
        result = execute_eql_query(query, board_id="rq_board", use_cache=False)
        self.assertIn("governance", result)
        self.assertEqual(result["governance"]["model_version"], "1.1")
        self.assertTrue(result["governance"]["cross_layer_validation"]["valid"])

    def test_reject_unregistered_metric(self) -> None:
        query = """
REPORT:
TYPE = EXECUTIVE
FILTER:
PERIOD = LAST_7_DAYS
METRICS:
BOGUS_KPI
LIMIT:
10
"""
        with self.assertRaises(InvalidFieldError):
            execute_eql_query(query, board_id="rq_board", use_cache=False)
