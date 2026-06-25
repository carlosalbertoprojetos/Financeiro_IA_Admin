"""CMGL validation and enforcer tests."""

from __future__ import annotations

from django.test import TestCase

from apps.intelligence.services.core_model.enforcer import (
    enforce_eql_ast,
    enforce_entity_type,
    enforce_metric,
    govern_pipeline,
)
from apps.intelligence.services.core_model.errors import (
    CrossLayerValidationError,
    UnregisteredEntityError,
    UnregisteredMetricError,
)
from apps.intelligence.services.core_model.validator import (
    validate_eql_ast,
    validate_semantic_output,
)


class ValidationTests(TestCase):
    def test_valid_eql_ast(self) -> None:
        ast = {
            "metrics": ["LEAD_TIME", "RISK_SCORE"],
            "semantic_filters": {"entity_type": {"values": ["INCIDENT"]}},
            "filters": {"period": {"preset": "LAST_30_DAYS"}},
        }
        validate_eql_ast(ast)

    def test_reject_invalid_metric(self) -> None:
        with self.assertRaises(CrossLayerValidationError):
            validate_eql_ast({"metrics": ["BOGUS_METRIC"], "filters": {}})

    def test_reject_invalid_entity(self) -> None:
        with self.assertRaises(CrossLayerValidationError):
            validate_eql_ast({
                "metrics": [],
                "semantic_filters": {"entity_type": {"values": ["UNKNOWN_ENTITY"]}},
            })

    def test_valid_semantic_output(self) -> None:
        output = {
            "entities": [{"entity_type": "INCIDENT", "card_id": "c1"}],
            "business_metrics": {"incident_rate": {"value": 10}},
            "timeline": {"events": []},
        }
        validate_semantic_output(output)

    def test_enforce_unregistered_entity(self) -> None:
        with self.assertRaises(UnregisteredEntityError):
            enforce_entity_type("NOT_A_REAL_TYPE")

    def test_enforce_unregistered_metric(self) -> None:
        with self.assertRaises(UnregisteredMetricError):
            enforce_metric("INVALID_KPI")

    def test_govern_pipeline_full(self) -> None:
        result = govern_pipeline(
            ast={"metrics": ["LEAD_TIME"], "filters": {}},
            query_plan={"metrics": ["LEAD_TIME"], "filters": []},
            output={
                "entities": [{"entity_type": "TASK", "card_id": "c1"}],
                "business_metrics": {},
                "timeline": {"events": []},
            },
            strict=False,
        )
        self.assertTrue(result["governed"])
        self.assertEqual(result["model_version"], "1.1")
