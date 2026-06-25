"""ECP — Evolution Control Plane tests."""

from __future__ import annotations

import os
from unittest import mock

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.intelligence.models import EvolutionLog
from apps.intelligence.services.evolution.compatibility.matrix import (
    CompatLevel,
    check_layer_compatibility,
    check_system_compatibility,
)
from apps.intelligence.services.evolution.compatibility.query_adapter import adapt_legacy_query, detect_query_version
from apps.intelligence.services.evolution.config import is_safe_mode
from apps.intelligence.services.evolution.impact_analyzer import analyze_change_impact
from apps.intelligence.services.evolution.pipeline.orchestrator import (
    prepare_query_for_execution,
    run_evolution_pipeline,
    validate_deployment,
)
from apps.intelligence.services.evolution.rollback.manager import list_rollback_targets, rollback_to_version
from apps.intelligence.services.evolution.semantic_migration import migrate_entity, migrate_metric_keys
from apps.intelligence.services.evolution.storage import get_evolution_history, log_evolution_event
from apps.intelligence.services.evolution.versioning.core import version_snapshot
from apps.intelligence.services.query_engine.runner import execute_eql_query
from apps.intelligence.tests.test_report_query import ReportQueryTestMixin


class VersioningCoreTests(TestCase):
    def test_system_version_snapshot(self) -> None:
        snap = version_snapshot()
        self.assertIn("system_version", snap)
        self.assertIn("layers", snap)
        self.assertIn("eql", snap["layers"])

    @mock.patch.dict(os.environ, {"EOR_SYSTEM_VERSION": "1.0.1"})
    def test_env_system_version(self) -> None:
        from apps.intelligence.services.evolution.versioning.core import get_system_version

        self.assertEqual(get_system_version(), "1.0.1")


class CompatibilityMatrixTests(TestCase):
    def test_same_version_ok(self) -> None:
        self.assertEqual(check_layer_compatibility("eql", "1.0.0", "1.0.0"), CompatLevel.OK)

    def test_major_break(self) -> None:
        self.assertEqual(check_layer_compatibility("eql", "1.0.0", "2.0.0"), CompatLevel.BREAK)

    def test_system_compatibility(self) -> None:
        result = check_system_compatibility("1.0.0")
        self.assertIn("layers", result)
        self.assertIn("overall", result)
        self.assertTrue(result["compatible"])


class QueryAdapterTests(TestCase):
    def test_detect_legacy_risk_syntax(self) -> None:
        query = "REPORT:\nTYPE = EXECUTIVE\nFILTER:\nRISK = HIGH"
        self.assertEqual(detect_query_version(query), "1.0.0")

    def test_adapt_risk_to_score(self) -> None:
        query = "REPORT:\nTYPE = EXECUTIVE\nFILTER:\nRISK = HIGH\nPERIOD:\nLAST_30_DAYS"
        adapted, changes = adapt_legacy_query(query, source_version="1.0.0")
        self.assertIn("RISK_SCORE", adapted)
        self.assertTrue(any(c["type"] == "field_migration" for c in changes))

    def test_modern_query_unchanged(self) -> None:
        query = "REPORT:\nTYPE = EXECUTIVE\nFILTER:\nENTITY_TYPE = INCIDENT\nPERIOD:\nLAST_7_DAYS\nLIMIT:\n50"
        adapted, changes = adapt_legacy_query(query, source_version="1.1.0")
        self.assertEqual(adapted, query)
        self.assertEqual(changes, [])

    def test_prepare_query_hook(self) -> None:
        query = "REPORT:\nTYPE = EXECUTIVE\nFILTER:\nRISK = HIGH\nPERIOD:\nLAST_30_DAYS"
        adapted, meta = prepare_query_for_execution(query)
        self.assertIn("detected_version", meta)
        self.assertIn("RISK_SCORE", adapted)


class SemanticMigrationTests(TestCase):
    def test_entity_type_migration(self) -> None:
        entity = {"entity_type": "FAILURE", "category": "OPS"}
        migrated, changes = migrate_entity(entity, from_version="1.0.0")
        self.assertEqual(migrated["entity_type"], "INCIDENT")
        self.assertIn("entity_type:FAILURE->INCIDENT", changes)

    def test_incident_reclassification(self) -> None:
        entity = {
            "entity_type": "INCIDENT",
            "risk_score": 80,
            "risk_flags": ["external_dependency"],
        }
        migrated, changes = migrate_entity(entity)
        self.assertEqual(migrated["entity_type"], "RISK_EVENT")
        self.assertTrue(any("reclassify" in c for c in changes))

    def test_metric_key_migration(self) -> None:
        metrics = {"FAILURE_RATE": 0.12, "RISK_SCORE": 55}
        migrated, changes = migrate_metric_keys(metrics)
        self.assertIn("incident_rate", migrated)
        self.assertTrue(any("FAILURE_RATE" in c for c in changes))


class ImpactAnalyzerTests(TestCase):
    def test_low_risk_upgrade(self) -> None:
        impact = analyze_change_impact(change_type="upgrade", from_version="1.0.0", to_version="1.0.0")
        self.assertEqual(impact["risk_level"], "LOW")
        self.assertEqual(impact["breaking_changes"], [])

    def test_legacy_query_detected(self) -> None:
        impact = analyze_change_impact(
            change_type="eql",
            from_version="1.0.0",
            sample_queries=["FILTER:\nRISK = HIGH"],
        )
        self.assertEqual(impact["risk_level"], "MEDIUM")
        self.assertTrue(impact["affected_queries"])

    def test_high_risk_major_upgrade(self) -> None:
        impact = analyze_change_impact(change_type="upgrade", from_version="1.0.0", to_version="2.0.0")
        self.assertEqual(impact["risk_level"], "HIGH")


class RollbackTests(TestCase):
    def test_list_targets(self) -> None:
        targets = list_rollback_targets()
        self.assertIn("1.0.0", targets)

    def test_rollback_creates_audit_log(self) -> None:
        manifest = rollback_to_version("1.0.0", initiated_by="test")
        self.assertEqual(manifest["status"], "rolled_back")
        self.assertEqual(EvolutionLog.objects.filter(change_type="rollback").count(), 1)

    def test_unknown_version_raises(self) -> None:
        with self.assertRaises(ValueError):
            rollback_to_version("9.9.9")


class SafeModeTests(TestCase):
    @override_settings()
    @mock.patch.dict(os.environ, {"EOR_SAFE_MODE": "true"})
    def test_safe_mode_blocks_high_risk(self) -> None:
        self.assertTrue(is_safe_mode())
        result = validate_deployment({
            "from_version": "1.0.0",
            "to_version": "2.0.0",
            "change_type": "upgrade",
        })
        self.assertFalse(result["approved"])
        self.assertEqual(EvolutionLog.objects.filter(status="rejected").count(), 1)

    @mock.patch.dict(os.environ, {"EOR_SAFE_MODE": "false"})
    def test_pipeline_approves_low_risk(self) -> None:
        result = run_evolution_pipeline({
            "from_version": "1.0.0",
            "to_version": "1.0.0",
            "change_type": "patch",
        })
        self.assertTrue(result["validation"]["approved"])


class EvolutionAuditLogTests(TestCase):
    def test_log_and_history(self) -> None:
        log_evolution_event(
            version_from="1.0.0",
            version_to="1.0.1",
            change_type="upgrade",
            affected_layers=["eql"],
            risk_assessment={"risk_level": "LOW"},
            status="completed",
        )
        history = get_evolution_history(limit=10)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["change_type"], "upgrade")


class EvolutionApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_overview(self) -> None:
        r = self.client.get("/api/evolution/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("endpoints", r.data)

    def test_version(self) -> None:
        r = self.client.get("/api/evolution/version/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("versions", r.data)

    def test_impact_adapt(self) -> None:
        r = self.client.post("/api/evolution/impact/", {
            "adapt_query": "REPORT:\nTYPE = EXECUTIVE\nFILTER:\nRISK = HIGH\nPERIOD:\nLAST_30_DAYS",
        }, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertIn("adapted_query", r.data)

    def test_flags(self) -> None:
        r = self.client.get("/api/evolution/flags/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("FEATURE_NEW_EQL_PARSER", r.data["flags"])

    def test_rollback_get(self) -> None:
        r = self.client.get("/api/evolution/rollback/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("targets", r.data)

    def test_history(self) -> None:
        r = self.client.get("/api/evolution/history/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("history", r.data)


class EvolutionRunnerIntegrationTests(ReportQueryTestMixin, TestCase):
    def test_legacy_query_executes_with_evolution_meta(self) -> None:
        query = """
REPORT:
TYPE = EXECUTIVE
FILTER:
RISK = HIGH
PERIOD = LAST_30_DAYS
LIMIT:
100
"""
        result = execute_eql_query(query, board_id="rq_board", use_cache=False)
        self.assertIn("evolution", result)
        self.assertIn("detected_version", result["evolution"])
        self.assertIn("trace_id", result)
