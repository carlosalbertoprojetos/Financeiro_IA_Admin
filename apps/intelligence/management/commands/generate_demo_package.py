from __future__ import annotations

import json

from django.core.management.base import BaseCommand

from apps.intelligence.services.document_generator.exporters.demo_package import build_demo_package
from apps.intelligence.services.report_query.output_contract import build_report_output_contract
from apps.intelligence.services.report_query.quality.fixtures import build_quality_gate_fixture


class Command(BaseCommand):
    help = "Generate EDG demo package from a fixture-derived output_contract."

    def add_arguments(self, parser):
        parser.add_argument("--output-dir", default="docs/demo_package")
        parser.add_argument("--theme", default="corporate")
        parser.add_argument("--json", action="store_true")

    def handle(self, *args, **options):
        report, _exports = build_quality_gate_fixture()
        output_contract = build_report_output_contract(report)
        result = build_demo_package(
            output_contract,
            output_dir=options["output_dir"],
            theme=options["theme"],
        )
        if options["json"]:
            self.stdout.write(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        else:
            self.stdout.write(f"{result['status']}: demo package written to {result['output_dir']}")
