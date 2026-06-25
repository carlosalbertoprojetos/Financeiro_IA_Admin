"""Semantic EQL and pipeline integration tests."""

from __future__ import annotations

from django.core.cache import cache
from django.test import TestCase

from apps.intelligence.services.eql.parser import parse_eql
from apps.intelligence.services.eql.validator import validate_eql
from apps.intelligence.services.query_engine.runner import execute_eql_query
from apps.intelligence.services.semantic_layer.pipeline import apply_semantic_layer
from apps.intelligence.services.semantic_layer.query_resolver import resolve_semantic_to_technical
from apps.intelligence.tests.test_report_query import ReportQueryTestMixin

SEMANTIC_EQL = """
REPORT:
TYPE = EXECUTIVE

FILTER:
PERIOD = LAST_30_DAYS
ENTITY_TYPE = INCIDENT
CATEGORY = FINANCEIRO
RISK_LEVEL >= HIGH
ENTITY_STATUS = ACTIVE

METRICS:
INCIDENT_RATE, RISK_EXPOSURE_INDEX

LIMIT:
100
"""


class SemanticEQLTests(TestCase):
    def test_parse_semantic_filters(self) -> None:
        q = parse_eql(SEMANTIC_EQL, board_id="b1")
        self.assertIn("entity_type", q.filters)
        self.assertIn("category", q.filters)
        self.assertIn("risk_level", q.filters)
        self.assertIn("entity_status", q.filters)

    def test_resolve_semantic_to_technical(self) -> None:
        validated = validate_eql(parse_eql(SEMANTIC_EQL, board_id="b1"))
        resolved, semantic = resolve_semantic_to_technical(validated)
        self.assertNotIn("entity_type", resolved.filters)
        self.assertIn("period", resolved.filters)
        self.assertIn("entity_type", semantic)
        self.assertIn("title_prefix", resolved.filters)

    def test_resolve_delivery_entity_type(self) -> None:
        validated = validate_eql(parse_eql(
            "REPORT:\nTYPE = EXECUTIVE\nFILTER:\nPERIOD = LAST_7_DAYS\nENTITY_TYPE = DELIVERY\nLIMIT:\n10",
            board_id="b1",
        ))
        resolved, semantic = resolve_semantic_to_technical(validated)
        self.assertIn("status", resolved.filters)


class SemanticPipelineTests(ReportQueryTestMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        cache.clear()

    def test_full_pipeline_with_semantic_output(self) -> None:
        result = execute_eql_query(SEMANTIC_EQL, board_id="rq_board", use_cache=False)
        self.assertIn("semantic", result)
        self.assertIn("business_metrics", result)
        self.assertIn("domain_insights", result)
        self.assertIn("entities", result)
        self.assertIn("incident_rate", result["business_metrics"])

    def test_semantic_layer_on_raw_output(self) -> None:
        raw = {
            "summary": {"board_id": "rq_board"},
            "cards": [{"card_id": "card_aqui", "risk_score": 70, "assignees": ["João"]}],
            "recommendations": [],
        }
        enriched = apply_semantic_layer(raw, cards=[self.card_aqui])
        self.assertTrue(enriched["entities"])
        self.assertIn("incident_rate", enriched["business_metrics"])
