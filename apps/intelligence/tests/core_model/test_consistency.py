"""CMGL semantic consistency tests."""

from __future__ import annotations

from django.test import TestCase

from apps.intelligence.services.core_model.semantic_consistency import (
    analyze_consistency,
    detect_entity_conflicts,
    detect_metric_conflicts,
)


class ConsistencyTests(TestCase):
    def test_detect_duplicate_metrics(self) -> None:
        conflicts = detect_metric_conflicts(["INCIDENT_RATE", "FAILURE_RATE"])
        self.assertTrue(any(c.conflict_type == "duplicate_metric" for c in conflicts))

    def test_detect_entity_overlap(self) -> None:
        entities = [
            {"card_id": "c1", "entity_type": "INCIDENT"},
            {"card_id": "c1", "entity_type": "DELIVERY"},
        ]
        conflicts = detect_entity_conflicts(entities)
        self.assertTrue(any(c.conflict_type == "overlapping_entity" for c in conflicts))

    def test_analyze_consistent_output(self) -> None:
        output = {
            "query_ast": {"metrics": ["LEAD_TIME"]},
            "entities": [{"entity_type": "INCIDENT", "card_id": "c1"}],
            "business_metrics": {"incident_rate": {"value": 5}},
        }
        result = analyze_consistency(output)
        self.assertTrue(result["consistent"])

    def test_analyze_unregistered_metric(self) -> None:
        output = {
            "query_ast": {"metrics": []},
            "entities": [],
            "business_metrics": {"unknown_kpi": {"value": 1}},
        }
        result = analyze_consistency(output)
        self.assertFalse(result["consistent"])

    def test_risk_score_warning(self) -> None:
        conflicts = detect_metric_conflicts(["RISK_SCORE", "RISK_EXPOSURE_INDEX"])
        self.assertTrue(any(c.conflict_type == "related_metrics" for c in conflicts))
