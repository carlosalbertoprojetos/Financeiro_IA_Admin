from __future__ import annotations

import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import OperationalError

from apps.intelligence.services.report_query.domain.filters import ExportFormat, ReportQueryPayload
from apps.intelligence.services.report_query.engine.executor import execute_report_query
from apps.intelligence.services.report_query.quality.baseline import (
    DEFAULT_BASELINE_FILE,
    compare_to_baseline,
    load_baseline,
    save_baseline,
)
from apps.intelligence.services.report_query.quality.fixtures import build_quality_gate_fixture
from apps.intelligence.services.report_query.quality.validator import validate_report_quality
from integrations.trello.models import Board


class Command(BaseCommand):
    help = "Validate decision value and executive quality of generated EOR reports."

    def add_arguments(self, parser):
        parser.add_argument("--board-id", help="Trello board id to validate.")
        parser.add_argument("--period", help="Report period preset for database mode.")
        parser.add_argument("--save-baseline", action="store_true", help="Save the current validation as baseline.")
        parser.add_argument("--compare-baseline", action="store_true", help="Compare current validation against baseline.")
        parser.add_argument("--baseline-file", default=DEFAULT_BASELINE_FILE, help="Baseline JSON file.")
        parser.add_argument("--tolerance", type=int, default=0, help="Allowed score drop when comparing baseline.")
        parser.add_argument("--fixture", action="store_true", help="Validate a built-in fixture without database access.")
        parser.add_argument(
            "--fixture-variant",
            default="complete",
            choices=("complete", "missing_story"),
            help="Fixture variant for quality gate validation.",
        )
        parser.add_argument("--json", action="store_true", help="Print full JSON payload.")

    def handle(self, *args, **options):
        if options["fixture"]:
            report, exports = build_quality_gate_fixture(variant=options["fixture_variant"])
            validation = validate_report_quality(report, exports=exports)
            validation["mode"] = "fixture"
            validation["fixture_variant"] = options["fixture_variant"]
            self._apply_baseline_options(validation, options)
            self._write_validation(validation, options["json"])
            if validation["status"] == "FAIL":
                raise CommandError("Report quality gate failed.")
            return

        try:
            board_id = options.get("board_id") or self._default_board_id()
            if not board_id:
                raise CommandError("FAIL: no board_id provided and no board found.")

            base_payload = ReportQueryPayload.from_dict(
                {
                    "board_id": board_id,
                    "period": options.get("period"),
                    "use_cache": False,
                }
            )
            report = execute_report_query(base_payload)
            exports = {"json": report}
            for fmt in (ExportFormat.MARKDOWN, ExportFormat.PDF, ExportFormat.PPTX):
                export_report = execute_report_query(
                    ReportQueryPayload.from_dict(
                        {
                            "board_id": board_id,
                            "period": options.get("period"),
                            "export_format": fmt.value,
                            "use_cache": False,
                        }
                    )
                )
                exports[fmt.value] = export_report.get("export", {})
        except OperationalError as exc:
            payload = {
                "status": "FAIL",
                "mode": "database",
                "decision_value_score": 0,
                "classification": "fraco",
                "failures": [f"database unavailable: {exc}"],
                "warnings": [],
                "database": self._database_diagnostics(),
                "instructions": [
                    "Start the PostgreSQL service/container configured for EOR.",
                    "Check POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER and POSTGRES_CONNECT_TIMEOUT.",
                    "For CI or local quick validation, run: EOR_TESTING=true python manage.py validate_report_quality --fixture --json",
                    "For staging/database validation, pass --board-id and optionally --period.",
                ],
            }
            if options["json"]:
                self.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
            else:
                self.stdout.write("FAIL: database unavailable")
            raise CommandError("Report quality gate failed: database unavailable.") from exc

        validation = validate_report_quality(report, exports=exports)
        validation["board_id"] = board_id
        validation["mode"] = "database"
        validation["period"] = options.get("period")
        validation["database"] = self._database_diagnostics()
        self._apply_baseline_options(validation, options)
        self._write_validation(validation, options["json"])

        if validation["status"] == "FAIL":
            raise CommandError("Report quality gate failed.")

    def _write_validation(self, validation: dict, as_json: bool) -> None:
        if as_json:
            self.stdout.write(json.dumps(validation, indent=2, ensure_ascii=False, default=str))
        else:
            self.stdout.write(
                f"{validation['status']}: DecisionValueScore="
                f"{validation['decision_value_score']} ({validation['classification']})"
            )
            for failure in validation["failures"]:
                self.stdout.write(f"FAIL: {failure}")
            for warning in validation["warnings"]:
                self.stdout.write(f"WARNING: {warning}")
            comparison = validation.get("baseline_comparison")
            if comparison:
                self.stdout.write(f"BASELINE: {comparison['status']}")
                for regression in comparison.get("regressions", []):
                    self.stdout.write(f"REGRESSION: {regression}")

    def _default_board_id(self) -> str:
        board = Board.objects.order_by("name").first()
        return board.trello_id if board else ""

    def _database_diagnostics(self) -> dict:
        db = settings.DATABASES.get("default", {})
        options = db.get("OPTIONS") or {}
        return {
            "engine": db.get("ENGINE"),
            "host": db.get("HOST"),
            "port": db.get("PORT"),
            "database": db.get("NAME"),
            "connect_timeout": options.get("connect_timeout"),
            "EOR_TESTING": os.environ.get("EOR_TESTING", ""),
            "POSTGRES_HOST": os.environ.get("POSTGRES_HOST", ""),
            "POSTGRES_PORT": os.environ.get("POSTGRES_PORT", ""),
            "POSTGRES_DB": os.environ.get("POSTGRES_DB", ""),
        }

    def _apply_baseline_options(self, validation: dict, options: dict) -> None:
        baseline_file = options.get("baseline_file") or DEFAULT_BASELINE_FILE
        validation["baseline_file"] = baseline_file

        if options.get("save_baseline"):
            validation["saved_baseline"] = save_baseline(validation, baseline_file)

        if options.get("compare_baseline"):
            try:
                baseline = load_baseline(baseline_file)
            except FileNotFoundError as exc:
                validation["baseline_comparison"] = {
                    "status": "FAIL",
                    "regressions": [str(exc)],
                    "scores": [],
                    "missing_sections": [],
                    "missing_exports": [],
                    "missing_checks": [],
                    "tolerance": options.get("tolerance", 0),
                }
                validation["status"] = "FAIL"
                validation.setdefault("failures", []).append(str(exc))
                return

            comparison = compare_to_baseline(
                validation,
                baseline,
                tolerance=options.get("tolerance", 0),
            )
            validation["baseline_comparison"] = comparison
            if comparison["status"] == "FAIL":
                validation["status"] = "FAIL"
                validation.setdefault("failures", []).extend(comparison["regressions"])
