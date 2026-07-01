from __future__ import annotations

import base64
import json
from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from apps.intelligence.services.report_query.domain.filters import ExportFormat, ReportQueryPayload
from apps.intelligence.services.report_query.engine.executor import execute_report_query
from integrations.trello.models import Action, Board, BoardList, Card, Member


class ReportAnalyticalQualityTests(TestCase):
    def setUp(self) -> None:
        cache.clear()
        self.board = Board.objects.create(trello_id="quality_board", name="Quality Board")
        self.backlog = BoardList.objects.create(
            trello_id="quality_backlog",
            board=self.board,
            name="Backlog",
            position=0,
        )
        self.doing = BoardList.objects.create(
            trello_id="quality_doing",
            board=self.board,
            name="Em Andamento",
            position=1,
        )
        self.done = BoardList.objects.create(
            trello_id="quality_done",
            board=self.board,
            name="Concluido",
            position=2,
        )
        self.ana = Member.objects.create(trello_id="ana", full_name="Ana")

        self.hotfix = Card.objects.create(
            trello_id="q_hotfix",
            board=self.board,
            board_list=self.doing,
            title="[URGENTE] Corrigir bug de relatório executivo",
            description=(
                "Objetivo: corrigir falha no PDF executivo. Prazo hoje. "
                "Responsavel Ana. Proximo passo validar exportacao."
            ),
            status="Em Andamento",
            due_at=timezone.now() - timedelta(days=1),
            last_activity_at=timezone.now() - timedelta(days=8),
            labels=[{"name": "Urgente"}, {"name": "Relatorio"}],
            raw_json={"badges": {"checkItems": 3, "checkItemsCheck": 1}},
        )
        self.hotfix.assignees.add(self.ana)

        self.infra = Card.objects.create(
            trello_id="q_infra",
            board=self.board,
            board_list=self.backlog,
            title="Ajustar worker e fila de sincronizacao",
            description="Servidor worker com fila instavel. Necessario monitoramento e decisao de capacidade.",
            status="Backlog",
            due_at=timezone.now() + timedelta(days=2),
            labels=[{"name": "Infra"}],
        )

        self.empty = Card.objects.create(
            trello_id="q_empty",
            board=self.board,
            board_list=self.backlog,
            title="Card sem contexto",
            description="",
            status="Backlog",
        )

        Action.objects.create(
            trello_id="q_comment",
            board=self.board,
            member=self.ana,
            action_type="commentCard",
            occurred_at=timezone.now() - timedelta(hours=2),
            raw_json={"data": {"card": {"id": "q_hotfix"}, "text": "Decisao: priorizar correcao antes do demo."}},
        )

    def test_report_includes_analytical_layer_with_evidence(self) -> None:
        result = execute_report_query(ReportQueryPayload(board_id="quality_board", use_cache=False))

        self.assertIn("analytical", result)
        self.assertGreater(result["report_quality_score"], 0)
        self.assertIn("report_quality_label", result)
        self.assertTrue(result["analytical"]["recommendations"])

        cards = {
            item["card_id"]: item
            for item in result["analytical"]["activity_classification"]["cards"]
        }
        self.assertEqual(cards["q_hotfix"]["activity_type"], "Correcao")
        self.assertGreaterEqual(cards["q_hotfix"]["activity_confidence"], 0.5)
        self.assertTrue(cards["q_hotfix"]["evidence"])
        self.assertEqual(cards["q_empty"]["activity_confidence"], 0.2)
        self.assertEqual(cards["q_empty"]["description_quality_score"], 0)

    def test_metrics_pack_tracks_sla_quality_communication_and_risk(self) -> None:
        result = execute_report_query(ReportQueryPayload(board_id="quality_board", use_cache=False))
        metrics = result["analytical"]["metrics_pack"]

        self.assertEqual(metrics["sla"]["overdue_open_cards"], 1)
        self.assertEqual(metrics["quality"]["missing_owner_count"], 2)
        self.assertEqual(metrics["quality"]["incomplete_description_count"], 1)
        self.assertEqual(metrics["communication"]["total_comments"], 1)
        self.assertGreaterEqual(len(metrics["risks"]["high_risk_cards"]), 1)

    def test_card_rows_expose_evidence_and_next_action(self) -> None:
        result = execute_report_query(ReportQueryPayload(board_id="quality_board", use_cache=False))
        rows = {item["card_id"]: item for item in result["cards"]}

        self.assertIn("activity_type", rows["q_hotfix"])
        self.assertIn("evidence", rows["q_hotfix"])
        self.assertIn("next_action", rows["q_hotfix"])
        self.assertTrue(rows["q_hotfix"]["next_action"])

    def test_exports_include_analytical_quality_payload(self) -> None:
        for export_format in (ExportFormat.CSV, ExportFormat.MARKDOWN, ExportFormat.PPTX):
            result = execute_report_query(
                ReportQueryPayload(
                    board_id="quality_board",
                    export_format=export_format,
                    use_cache=False,
                )
            )
            content = base64.b64decode(result["export"]["content_base64"]).decode("utf-8-sig")
            if export_format == ExportFormat.CSV:
                self.assertIn("activity_type", content)
                self.assertIn("next_action", content)
            elif export_format == ExportFormat.MARKDOWN:
                self.assertIn("Qualidade analítica", content)
                self.assertIn("Recomendações", content)
            else:
                payload = json.loads(content)
                self.assertIn("report_quality", payload)
                self.assertIn("recommendations", payload)

    def test_executive_narrative_has_evidence_and_readability_score(self) -> None:
        result = execute_report_query(ReportQueryPayload(board_id="quality_board", use_cache=False))
        narrative = result["executive_narrative"]

        self.assertGreater(narrative["executive_readability_score"]["score"], 0)
        self.assertTrue(narrative["insights"])
        self.assertTrue(narrative["root_cause_hypotheses"])
        self.assertTrue(narrative["management_decisions"])
        for key, section in narrative["sections"].items():
            if key == "readability_inputs":
                continue
            self.assertTrue(section["summary"])
            self.assertTrue(section["evidence"])

    def test_insights_are_prioritized_and_have_required_fields(self) -> None:
        result = execute_report_query(ReportQueryPayload(board_id="quality_board", use_cache=False))
        insights = result["executive_narrative"]["insights"]
        required = {
            "title",
            "severity",
            "metric_source",
            "evidence",
            "affected_area",
            "business_impact",
            "recommended_action",
            "confidence",
        }
        rank_values = [
            (
                item["_rank"]["risk"],
                item["_rank"]["impact"],
                item["_rank"]["urgency"],
                item["_rank"]["recurrence"],
            )
            for item in insights
        ]

        self.assertEqual(rank_values, sorted(rank_values, reverse=True))
        for insight in insights:
            self.assertTrue(required.issubset(insight.keys()))
            self.assertTrue(insight["evidence"])
            self.assertTrue(insight["recommended_action"])

    def test_root_causes_and_management_decisions_are_actionable(self) -> None:
        result = execute_report_query(ReportQueryPayload(board_id="quality_board", use_cache=False))
        narrative = result["executive_narrative"]

        for hypothesis in narrative["root_cause_hypotheses"]:
            self.assertTrue(hypothesis["evidence"])
            self.assertTrue(hypothesis["how_to_validate"])
            self.assertTrue(hypothesis["recommended_action"])

        for decision in narrative["management_decisions"]:
            self.assertTrue(decision["decision"])
            self.assertTrue(decision["reason"])
            self.assertTrue(decision["expected_impact"])
            self.assertTrue(decision["suggested_owner"])
            self.assertTrue(decision["suggested_deadline"])

    def test_narrative_exports_include_executive_sections(self) -> None:
        markdown = execute_report_query(
            ReportQueryPayload(
                board_id="quality_board",
                export_format=ExportFormat.MARKDOWN,
                use_cache=False,
            )
        )
        md_content = base64.b64decode(markdown["export"]["content_base64"]).decode("utf-8-sig")
        self.assertIn("Narrativa Executiva", md_content)
        self.assertIn("Diagnostico Executivo", md_content)

        pptx = execute_report_query(
            ReportQueryPayload(
                board_id="quality_board",
                export_format=ExportFormat.PPTX,
                use_cache=False,
            )
        )
        outline = json.loads(base64.b64decode(pptx["export"]["content_base64"]).decode("utf-8-sig"))
        self.assertEqual([slide["title"] for slide in outline["slides"][:9]], [
            "Capa",
            "Executive Brief",
            "Scorecard Executivo",
            "Top 3 Drivers",
            "Riscos se Nada Mudar",
            "Gargalos",
            "Decisões recomendadas",
            "Plano de Ação",
            "Anexo Analítico",
        ])
        self.assertIn("Descobertas", [slide["title"] for slide in outline["slides"]])
        self.assertIn("executive_readability", outline)
