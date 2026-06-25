"""CMGL versioning tests."""

from __future__ import annotations

from django.test import TestCase

from apps.intelligence.services.core_model.dictionary import get_term, resolve_canonical_entity
from apps.intelligence.services.core_model.versioning import (
    check_compatibility,
    get_current_version,
    migrate_metric_name,
)


class VersioningTests(TestCase):
    def test_current_version(self) -> None:
        self.assertEqual(get_current_version(), "1.1")

    def test_compatible_version(self) -> None:
        result = check_compatibility("1.1", entity_types=["INCIDENT"], metrics=["LEAD_TIME"])
        self.assertTrue(result.compatible)

    def test_incompatible_entity(self) -> None:
        result = check_compatibility("1.0", entity_types=["BOTTLENECK"])
        self.assertFalse(result.compatible)
        self.assertIn("BOTTLENECK", result.missing_entities)

    def test_unknown_version(self) -> None:
        result = check_compatibility("99.0")
        self.assertFalse(result.compatible)

    def test_migrate_metric_name(self) -> None:
        self.assertEqual(migrate_metric_name("FAILURE_RATE", "1.0"), "INCIDENT_RATE")

    def test_dictionary_incident(self) -> None:
        term = get_term("INCIDENT")
        assert term is not None
        self.assertIn("impacto negativo", term["definition"])
        self.assertEqual(resolve_canonical_entity("INCIDENT"), "INCIDENT")

    def test_dictionary_blocker(self) -> None:
        self.assertEqual(resolve_canonical_entity("BLOCKER"), "BOTTLENECK")
