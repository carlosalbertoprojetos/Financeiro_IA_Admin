"""CMGL registry tests."""

from __future__ import annotations

from django.test import TestCase

from apps.intelligence.services.core_model.registry import REGISTRY


class RegistryTests(TestCase):
    def test_entity_types_registered(self) -> None:
        self.assertIn("INCIDENT", REGISTRY.entity_types)
        self.assertIn("DELIVERY", REGISTRY.entity_types)
        self.assertIn("PROJECT", REGISTRY.entity_types)

    def test_resolve_entity_alias(self) -> None:
        self.assertEqual(REGISTRY.resolve_entity_type("FAILURE"), "INCIDENT")
        self.assertEqual(REGISTRY.resolve_entity_type("BLOCKER"), "BOTTLENECK")

    def test_metrics_registered(self) -> None:
        self.assertIn("LEAD_TIME", REGISTRY.metrics)
        self.assertIn("INCIDENT_RATE", REGISTRY.metrics)

    def test_resolve_metric_alias(self) -> None:
        self.assertEqual(REGISTRY.resolve_metric("FAILURE_RATE"), "INCIDENT_RATE")

    def test_normalize_snake_case_metric(self) -> None:
        self.assertEqual(REGISTRY.normalize_metric_key("incident_rate"), "INCIDENT_RATE")

    def test_events_registered(self) -> None:
        self.assertTrue(REGISTRY.is_event_registered("CARD_MOVED"))

    def test_registry_to_dict(self) -> None:
        d = REGISTRY.to_dict()
        self.assertIn("entity_types", d)
        self.assertIn("metrics", d)

    def test_register_extension(self) -> None:
        REGISTRY.register_extension("custom_field", {"type": "string"})
        self.assertIn("custom_field", REGISTRY.extensions)
