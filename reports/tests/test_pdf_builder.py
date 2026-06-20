from datetime import datetime, timezone

from django.test import SimpleTestCase

from reports.engine.pdf_builder import build_executive_report_pdf
from reports.exceptions import ReportValidationError


class ExecutiveReportPdfTests(SimpleTestCase):
    def setUp(self):
        self.metrics = {
            "board_id": "board-1",
            "generated_at": datetime(2026, 6, 10, tzinfo=timezone.utc).isoformat(),
            "overview": {
                "board_id": "board-1",
                "generated_at": datetime(2026, 6, 10, tzinfo=timezone.utc).isoformat(),
                "counts": {
                    "total_cards": 12,
                    "open_cards": 7,
                    "completed_cards": 5,
                },
                "kpis": {
                    "lead_time": {
                        "metric": "lead_time",
                        "unit": "hours",
                        "summary": {"count": 5, "mean": 72.0, "median": 68.0, "p90": 96.0},
                    },
                    "cycle_time": {
                        "metric": "cycle_time",
                        "unit": "hours",
                        "summary": {"count": 5, "mean": 48.0, "median": 45.0, "p90": 60.0},
                    },
                    "aging": {
                        "metric": "aging",
                        "unit": "hours",
                        "summary": {"count": 7, "mean": 36.0, "median": 30.0, "p90": 72.0},
                    },
                    "throughput": {
                        "metric": "throughput",
                        "unit": "cards",
                        "summary": {"total_completed": 5, "periods": 3, "average_per_period": 1.67},
                        "series": [
                            {"period": "2026-06-08", "count": 2},
                            {"period": "2026-06-09", "count": 1},
                            {"period": "2026-06-10", "count": 2},
                        ],
                    },
                    "delay_rate": {
                        "metric": "delay_rate",
                        "unit": "ratio",
                        "summary": {
                            "total_with_due_date": 8,
                            "delayed": 2,
                            "delay_rate_pct": 25.0,
                        },
                    },
                    "rework_rate": {
                        "metric": "rework_rate",
                        "unit": "ratio",
                        "summary": {
                            "cards_with_rework": 1,
                            "rework_rate_pct": 10.0,
                        },
                    },
                },
            },
        }
        self.diagnosis = {
            "executive_summary": "O fluxo apresenta atrasos moderados e oportunidade de reduzir aging.",
            "problems": [
                {
                    "title": "Atrasos em due dates",
                    "description": "25% dos cards com prazo estão atrasados.",
                    "severity": "medium",
                }
            ],
            "risks": [
                {
                    "title": "Capacidade",
                    "description": "WIP elevado pode degradar throughput.",
                    "impact": "high",
                    "likelihood": "medium",
                }
            ],
            "recommendations": [
                {
                    "title": "Limitar WIP",
                    "action": "Definir limites por coluna.",
                    "priority": "high",
                    "expected_outcome": "Menor aging e lead time.",
                }
            ],
        }

    def test_build_executive_report_pdf(self):
        pdf_bytes = build_executive_report_pdf(
            self.metrics,
            self.diagnosis,
            board_name="Board Demo",
        )
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 1000)

    def test_build_executive_report_pdf_requires_diagnosis_keys(self):
        with self.assertRaises(ReportValidationError):
            build_executive_report_pdf(self.metrics, {"executive_summary": "only summary"})

    def test_build_executive_report_pdf_requires_overview(self):
        with self.assertRaises(ReportValidationError):
            build_executive_report_pdf({"board_id": "x"}, self.diagnosis)
