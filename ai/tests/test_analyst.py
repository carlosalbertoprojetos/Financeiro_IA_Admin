import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

from django.test import SimpleTestCase, override_settings

from ai.analyst import analyze_metrics, compact_metrics
from ai.exceptions import AIAnalysisError, AIConfigurationError


class AnalystTests(SimpleTestCase):
    def setUp(self):
        self.metrics = {
            "board_id": "board-1",
            "generated_at": datetime(2026, 6, 10, tzinfo=timezone.utc).isoformat(),
            "overview": {
                "board_id": "board-1",
                "counts": {"total_cards": 10, "open_cards": 6, "completed_cards": 4},
                "kpis": {
                    "lead_time": {
                        "metric": "lead_time",
                        "unit": "hours",
                        "summary": {"count": 4, "mean": 80.0, "p90": 120.0},
                        "items": [{"card_id": "c1", "lead_time_hours": 80.0}],
                    },
                    "delay_rate": {
                        "metric": "delay_rate",
                        "unit": "ratio",
                        "summary": {"delay_rate_pct": 25.0, "delayed": 2, "total_with_due_date": 8},
                        "items": [],
                    },
                },
            },
            "gaps": {
                "summary": {"total_gaps": 3, "delayed_count": 2, "aging_high_count": 1},
                "gaps": {
                    "delayed": [{"card_id": "c2", "title": "Late card"}],
                    "aging_high": [],
                    "rework": [],
                    "unassigned_open": [],
                },
            },
        }

        self.mock_diagnosis = {
            "executive_summary": "O board apresenta atrasos moderados e aging elevado em parte do WIP.",
            "problems": [
                {
                    "title": "Atrasos recorrentes",
                    "description": "25% dos cards com due date estão atrasados.",
                    "severity": "medium",
                    "evidence": "delay_rate_pct=25",
                }
            ],
            "risks": [
                {
                    "title": "Acúmulo de WIP",
                    "description": "Cards envelhecendo no fluxo.",
                    "impact": "high",
                    "likelihood": "medium",
                }
            ],
            "recommendations": [
                {
                    "title": "Limitar WIP",
                    "action": "Definir WIP máximo por coluna.",
                    "priority": "high",
                    "expected_outcome": "Redução de aging e lead time.",
                }
            ],
        }

    def test_compact_metrics_strips_heavy_items(self):
        compact = compact_metrics(self.metrics)
        self.assertNotIn("items", compact["overview"]["kpis"]["lead_time"])
        self.assertEqual(compact["gaps"]["gaps"]["delayed"]["count"], 1)

    @override_settings(OPENAI_API_KEY="")
    def test_analyze_metrics_requires_api_key(self):
        with self.assertRaises(AIConfigurationError):
            analyze_metrics(self.metrics)

    def test_analyze_metrics_with_mock_client(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps(self.mock_diagnosis)))]
        mock_client.chat.completions.create.return_value = mock_response

        result = analyze_metrics(
            self.metrics,
            api_key="test-key",
            client=mock_client,
        )

        self.assertEqual(result["board_id"], "board-1")
        self.assertEqual(result["executive_summary"], self.mock_diagnosis["executive_summary"])
        self.assertEqual(len(result["problems"]), 1)
        self.assertEqual(len(result["recommendations"]), 1)
        mock_client.chat.completions.create.assert_called_once()

    def test_analyze_metrics_invalid_json_response(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="not-json"))]
        mock_client.chat.completions.create.return_value = mock_response

        with self.assertRaises(AIAnalysisError):
            analyze_metrics(self.metrics, api_key="test-key", client=mock_client)

    def test_analyze_metrics_missing_required_keys(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps({"executive_summary": "ok"})))]
        mock_client.chat.completions.create.return_value = mock_response

        with self.assertRaises(AIAnalysisError):
            analyze_metrics(self.metrics, api_key="test-key", client=mock_client)
