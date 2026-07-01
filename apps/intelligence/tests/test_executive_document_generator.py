from __future__ import annotations

import json
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

from django.core.management import call_command
from django.test import SimpleTestCase

from apps.intelligence.services.document_generator.builders import (
    build_executive_docx,
    build_executive_pdf,
    build_executive_pptx,
    build_executive_xlsx,
)
from apps.intelligence.services.document_generator.charts.factory import build_chart_specs
from apps.intelligence.services.document_generator.exporters.demo_package import build_demo_package
from apps.intelligence.services.document_generator.presentation import PresentationModel
from apps.intelligence.services.document_generator.templates.themes import get_theme
from apps.intelligence.services.document_generator.validators import (
    validate_docx,
    validate_pdf,
    validate_pptx,
    validate_xlsx,
)
from apps.intelligence.services.report_query.output_contract import build_report_output_contract
from apps.intelligence.services.report_query.quality.fixtures import build_quality_gate_fixture


class ExecutiveDocumentGeneratorTests(SimpleTestCase):
    def setUp(self) -> None:
        report, _exports = build_quality_gate_fixture()
        self.output_contract = build_report_output_contract(report)
        self.model = PresentationModel.from_output_contract(
            self.output_contract,
            theme=get_theme("executive"),
        ).with_charts(build_chart_specs(self.output_contract))

    def test_presentation_model_consumes_only_output_contract(self) -> None:
        self.assertEqual(len(self.model.kpis), 5)
        self.assertTrue(self.model.tables["kpis_principais"])
        self.assertTrue(self.model.rankings["top_10_risks"])
        self.assertIn("Executive Brief", self.model.sections)

    def test_pdf_docx_xlsx_and_pptx_validate(self) -> None:
        pdf = build_executive_pdf(self.model)
        pptx = build_executive_pptx(self.model)
        xlsx = build_executive_xlsx(self.model)
        docx = build_executive_docx(self.model)

        self.assertEqual(validate_pdf(pdf, expected_sections=set(self.model.sections))["status"], "PASS")
        self.assertEqual(validate_pptx(pptx)["status"], "PASS")
        self.assertEqual(validate_xlsx(xlsx)["status"], "PASS")
        self.assertEqual(validate_docx(docx)["status"], "PASS")

    def test_pptx_golden_structure_has_minimum_slides(self) -> None:
        content = build_executive_pptx(self.model)
        with zipfile.ZipFile(BytesIO(content)) as package:
            slides = [name for name in package.namelist() if name.startswith("ppt/slides/slide")]
            presentation = package.read("ppt/presentation.xml").decode("utf-8")

        self.assertEqual(len([name for name in slides if name.endswith(".xml")]), 12)
        self.assertIn("rId12", presentation)

    def test_demo_package_writes_all_artifacts_from_same_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_demo_package(self.output_contract, output_dir=tmpdir)
            files = {path.name for path in Path(tmpdir).iterdir()}

        self.assertEqual(result["status"], "PASS")
        self.assertTrue(
            {
                "executive_report.pdf",
                "executive_report.pptx",
                "executive_report.xlsx",
                "executive_report.docx",
                "executive_report.json",
                "executive_report.md",
                "validation.json",
            }.issubset(files)
        )

    def test_generate_demo_package_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            call_command("generate_demo_package", output_dir=tmpdir, json=True)
            validation = json.loads((Path(tmpdir) / "validation.json").read_text(encoding="utf-8"))

        self.assertEqual(validation["pdf"]["status"], "PASS")
        self.assertEqual(validation["pptx"]["status"], "PASS")
        self.assertEqual(validation["xlsx"]["status"], "PASS")
        self.assertEqual(validation["docx"]["status"], "PASS")
