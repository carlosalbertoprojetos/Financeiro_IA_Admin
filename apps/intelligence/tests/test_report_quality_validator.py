from __future__ import annotations

from copy import deepcopy
from datetime import timedelta
from io import StringIO
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import OperationalError
from django.test import TestCase
from django.utils import timezone

from apps.intelligence.services.report_query.domain.filters import ExportFormat, ReportQueryPayload
from apps.intelligence.services.report_query.engine.executor import execute_report_query
from apps.intelligence.services.report_query.quality.validator import validate_report_quality
from integrations.trello.models import Action, Board, BoardList, Card, Member


class ReportQualityValidatorTests(TestCase):
    def setUp(self) -> None:
        cache.clear()
        self.board = Board.objects.create(trello_id="quality_gate_board", name="Quality Gate Board")
        self.doing = BoardList.objects.create(
            trello_id="quality_gate_doing",
            board=self.board,
            name="Em Andamento",
            position=1,
        )
        self.backlog = BoardList.objects.create(
            trello_id="quality_gate_backlog",
            board=self.board,
            name="Backlog",
            position=0,
        )
        self.member = Member.objects.create(trello_id="quality_gate_ana", full_name="Ana")
        now = timezone.now()

        for index in range(7):
            card = Card.objects.create(
                trello_id=f"quality_gate_card_{index}",
                board=self.board,
                board_list=self.doing if index < 5 else self.backlog,
                title=f"[URGENTE] Corrigir incidente sistema erp projeto alpha {index}",
                description="" if index < 4 else (
                    "Objetivo: estabilizar incidente. Prazo definido. "
                    "Responsavel Ana. Proximo passo validar correcao."
                ),
                status="Em Andamento",
                due_at=now - timedelta(days=1) if index < 4 else now + timedelta(days=2),
                last_activity_at=now - timedelta(days=8) if index < 4 else now,
                labels=[{"name": "Incidente"}],
                raw_json={"badges": {"checkItems": 2, "checkItemsCheck": 0 if index < 4 else 2}},
            )
            if index >= 4:
                card.assignees.add(self.member)
            Card.objects.filter(pk=card.pk).update(
                created_at=now - timedelta(days=10 if index < 2 else 1),
                updated_at=now - timedelta(days=8 if index < 4 else 1),
            )
            if index < 3:
                Action.objects.create(
                    trello_id=f"quality_gate_comment_{index}",
                    board=self.board,
                    member=self.member,
                    action_type="commentCard",
                    occurred_at=now - timedelta(hours=index + 1),
                    raw_json={
                        "data": {
                            "card": {"id": f"quality_gate_card_{index}"},
                            "text": "Decisao: tratar incidente antes de novas demandas.",
                        }
                    },
                )

    def _report_and_exports(self):
        report = execute_report_query(ReportQueryPayload(board_id="quality_gate_board", use_cache=False))
        exports = {"json": report}
        for fmt in (ExportFormat.MARKDOWN, ExportFormat.PDF, ExportFormat.PPTX):
            exported = execute_report_query(
                ReportQueryPayload(
                    board_id="quality_gate_board",
                    export_format=fmt,
                    use_cache=False,
                )
            )
            exports[fmt.value] = exported["export"]
        return report, exports

    def test_decision_value_score_passes_for_complete_report(self) -> None:
        report, exports = self._report_and_exports()
        validation = validate_report_quality(report, exports=exports)

        self.assertIn(validation["status"], {"PASS", "WARNING"})
        self.assertGreaterEqual(validation["decision_value_score"], 70)
        self.assertIn(validation["classification"], {"bom", "executivo"})
        self.assertTrue(validation["checks"]["executive_story_present"])
        self.assertTrue(validation["checks"]["exports_carry_narrative"])

    def test_fails_when_executive_story_is_missing(self) -> None:
        report, exports = self._report_and_exports()
        broken = deepcopy(report)
        broken.pop("executive_story", None)
        broken.pop("executive_story_quality_score", None)

        validation = validate_report_quality(broken, exports=exports)

        self.assertEqual(validation["status"], "FAIL")
        self.assertIn("executive_story ausente ou nao gerado", validation["failures"])

    def test_fails_when_decisions_have_no_evidence(self) -> None:
        report, exports = self._report_and_exports()
        broken = deepcopy(report)
        for decision in broken["executive_story"]["decision_ready_summary"]:
            decision["evidence"] = []

        validation = validate_report_quality(broken, exports=exports)

        self.assertEqual(validation["status"], "FAIL")
        self.assertIn("decisoes sem evidencia", validation["failures"])

    def test_export_validation_detects_missing_blocks(self) -> None:
        report, exports = self._report_and_exports()
        broken_exports = deepcopy(exports)
        broken_exports["markdown"] = {
            **broken_exports["markdown"],
            "content_base64": "",
        }

        validation = validate_report_quality(report, exports=broken_exports)

        self.assertEqual(validation["status"], "FAIL")
        self.assertFalse(validation["checks"]["exports_carry_narrative"])

    def test_validate_report_quality_command_passes_for_complete_report(self) -> None:
        stdout = StringIO()

        call_command(
            "validate_report_quality",
            board_id="quality_gate_board",
            stdout=stdout,
        )

        self.assertIn("DecisionValueScore", stdout.getvalue())

    def test_fixture_mode_passes_without_database(self) -> None:
        stdout = StringIO()

        call_command(
            "validate_report_quality",
            fixture=True,
            json=True,
            stdout=stdout,
        )
        payload = json.loads(stdout.getvalue())

        self.assertEqual(payload["mode"], "fixture")
        self.assertEqual(payload["status"], "PASS")
        self.assertGreaterEqual(payload["decision_value_score"], 70)

    def test_fixture_mode_fails_when_executive_story_missing(self) -> None:
        stdout = StringIO()

        with self.assertRaises(CommandError):
            call_command(
                "validate_report_quality",
                fixture=True,
                fixture_variant="missing_story",
                json=True,
                stdout=stdout,
            )
        payload = json.loads(stdout.getvalue().split("CommandError")[0])

        self.assertEqual(payload["mode"], "fixture")
        self.assertEqual(payload["status"], "FAIL")
        self.assertIn("executive_story ausente ou nao gerado", payload["failures"])

    def test_database_unavailable_returns_controlled_json_failure(self) -> None:
        stdout = StringIO()

        with patch(
            "apps.intelligence.management.commands.validate_report_quality.Command._default_board_id",
            side_effect=OperationalError("connection timeout expired"),
        ):
            with self.assertRaises(CommandError):
                call_command(
                    "validate_report_quality",
                    json=True,
                    stdout=stdout,
                )
        payload = json.loads(stdout.getvalue())

        self.assertEqual(payload["mode"], "database")
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["decision_value_score"], 0)
        self.assertIn("database unavailable", payload["failures"][0])
        self.assertIn("instructions", payload)

    def test_save_baseline_writes_current_fixture_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_file = str(Path(tmpdir) / "baseline.json")
            stdout = StringIO()

            call_command(
                "validate_report_quality",
                fixture=True,
                save_baseline=True,
                baseline_file=baseline_file,
                json=True,
                stdout=stdout,
            )
            payload = json.loads(stdout.getvalue())
            baseline = json.loads(Path(baseline_file).read_text(encoding="utf-8"))

            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(baseline["minimum_scores"]["DecisionValueScore"], payload["decision_value_score"])
            self.assertIn("required_exports", baseline)

    def test_compare_baseline_passes_for_current_fixture(self) -> None:
        stdout = StringIO()

        call_command(
            "validate_report_quality",
            fixture=True,
            compare_baseline=True,
            json=True,
            stdout=stdout,
        )
        payload = json.loads(stdout.getvalue())

        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["baseline_comparison"]["status"], "PASS")

    def test_compare_baseline_fails_when_scores_regress(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_file = Path(tmpdir) / "high-baseline.json"
            baseline_file.write_text(
                json.dumps(
                    {
                        "baseline_date": "2026-06-27",
                        "eor_model": "1.1",
                        "minimum_scores": {
                            "DecisionValueScore": 100,
                            "ReportQualityScore": 100,
                            "ReportIntelligenceScore": 100,
                            "ExecutiveStoryQualityScore": 100,
                        },
                        "required_sections": [],
                        "required_exports": ["json", "markdown", "pdf", "pptx"],
                        "required_checks": [],
                    }
                ),
                encoding="utf-8",
            )
            stdout = StringIO()

            with self.assertRaises(CommandError):
                call_command(
                    "validate_report_quality",
                    fixture=True,
                    compare_baseline=True,
                    baseline_file=str(baseline_file),
                    json=True,
                    stdout=stdout,
                )
            payload = json.loads(stdout.getvalue())

            self.assertEqual(payload["status"], "FAIL")
            self.assertEqual(payload["baseline_comparison"]["status"], "FAIL")
            self.assertTrue(payload["baseline_comparison"]["regressions"])

    def test_compare_baseline_tolerance_allows_small_score_drop(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_file = Path(tmpdir) / "tolerated-baseline.json"
            baseline_file.write_text(
                json.dumps(
                    {
                        "baseline_date": "2026-06-27",
                        "eor_model": "1.1",
                        "minimum_scores": {
                            "DecisionValueScore": 100,
                            "ReportQualityScore": 87,
                            "ReportIntelligenceScore": 91,
                            "ExecutiveStoryQualityScore": 93,
                        },
                        "required_sections": [],
                        "required_exports": ["json", "markdown", "pdf", "pptx"],
                        "required_checks": [],
                    }
                ),
                encoding="utf-8",
            )
            stdout = StringIO()

            call_command(
                "validate_report_quality",
                fixture=True,
                compare_baseline=True,
                baseline_file=str(baseline_file),
                tolerance=5,
                json=True,
                stdout=stdout,
            )
            payload = json.loads(stdout.getvalue())

            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["baseline_comparison"]["status"], "PASS")

    def test_compare_baseline_missing_file_is_friendly_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout = StringIO()
            missing = str(Path(tmpdir) / "missing.json")

            with self.assertRaises(CommandError):
                call_command(
                    "validate_report_quality",
                    fixture=True,
                    compare_baseline=True,
                    baseline_file=missing,
                    json=True,
                    stdout=stdout,
                )
            payload = json.loads(stdout.getvalue())

            self.assertEqual(payload["status"], "FAIL")
            self.assertIn("Baseline file not found", payload["failures"][0])
