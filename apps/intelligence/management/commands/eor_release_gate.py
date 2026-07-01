from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from apps.intelligence.services.product_readiness.connectors import connector_readiness
from apps.intelligence.services.product_readiness.diagnostics import multi_tenant_audit, system_health
from apps.intelligence.services.product_readiness.licensing import plan_catalog
from apps.intelligence.services.product_readiness.workspace import validate_workspace


class Command(BaseCommand):
    help = "Run the EOR commercial release gate."

    def add_arguments(self, parser):
        parser.add_argument("--output", default="docs/RELEASE_GATE_REPORT.md")
        parser.add_argument("--run-tests", action="store_true", help="Run critical test suite with EOR_TESTING=true.")

    def handle(self, *args, **options):
        checks = [
            _check("workspace", validate_workspace()),
            _check("migrations", _migration_status()),
            _check("health", system_health()),
            _check("tenant_isolation", multi_tenant_audit()),
            _check("licensing", plan_catalog()),
            _check("connectors", connector_readiness()),
        ]
        if options["run_tests"]:
            checks.append(_check("critical_tests", _run_critical_tests()))
        else:
            checks.append(
                {
                    "name": "critical_tests",
                    "status": "WARNING",
                    "payload": {"detail": "Not executed. Run with --run-tests before paid pilot."},
                }
            )

        final = _final_status(checks)
        report = {"status": final, "checks": checks}
        _write_report(Path(settings.BASE_DIR) / options["output"], report)
        self.stdout.write(final)


def _check(name: str, payload: dict) -> dict:
    status = str(payload.get("status", "")).lower()
    if status in ("ready", "ok"):
        gate_status = "READY"
    elif status in ("degraded", "warning", "attention_required"):
        gate_status = "WARNING"
    else:
        gate_status = "BLOCKED"
    return {"name": name, "status": gate_status, "payload": payload}


def _migration_status() -> dict:
    try:
        if os.environ.get("EOR_TESTING", "").lower() in ("true", "1", "yes"):
            call_command("migrate", verbosity=0, interactive=False)
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        return {"status": "ok" if not plan else "blocked", "unapplied_migrations": [str(item[0]) for item in plan]}
    except Exception as exc:
        return {"status": "blocked", "error": str(exc)}


def _run_critical_tests() -> dict:
    env = dict(os.environ)
    env["EOR_TESTING"] = "true"
    cmd = [
        sys.executable,
        "manage.py",
        "test",
        "apps.intelligence.tests.product_readiness",
    ]
    result = subprocess.run(
        cmd,
        cwd=str(settings.BASE_DIR),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=180,
    )
    return {
        "status": "ok" if result.returncode == 0 else "blocked",
        "returncode": result.returncode,
        "output_tail": result.stdout[-4000:],
    }


def _final_status(checks: list[dict]) -> str:
    if any(check["status"] == "BLOCKED" for check in checks):
        return "BLOCKED"
    if any(check["status"] == "WARNING" for check in checks):
        return "WARNING"
    return "READY"


def _write_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Release Gate Report",
        "",
        f"Status: **{report['status']}**",
        "",
        "```json",
        json.dumps(report, indent=2, default=str),
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
