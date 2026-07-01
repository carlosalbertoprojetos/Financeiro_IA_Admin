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


class ReportOutputRebuildTests(TestCase):
    def setUp(self) -> None:
        cache.clear()
        self.board = Board.objects.create(trello_id="output_board", name="Output Board")
        backlog = BoardList.objects.create(trello_id="output_backlog", board=self.board, name="Backlog", position=0)
        doing = BoardList.objects.create(trello_id="output_doing", board=self.board, name="Em Andamento", position=1)
        done = BoardList.objects.create(trello_id="output_done", board=self.board, name="Concluido", position=2)
        ana = Member.objects.create(trello_id="output_ana", full_name="Ana")
        bruno = Member.objects.create(trello_id="output_bruno", full_name="Bruno")
        now = timezone.now()

        cards = [
            (
                "out_1",
                doing,
                "[URGENTE] Corrigir incidente relatorio financeiro",
                "Objetivo corrigir bug do PDF executivo. Prazo hoje. Responsavel Ana. Proximo passo validar export.",
                now - timedelta(days=1),
                [ana],
                [{"name": "Relatorio"}],
            ),
            (
                "out_2",
                backlog,
                "Integracao fiscal sem responsavel",
                "Necessario integrar rotina fiscal e decidir capacidade.",
                now + timedelta(days=1),
                [],
                [{"name": "Integracao"}],
            ),
            (
                "out_3",
                backlog,
                "Card sem contexto",
                "",
                None,
                [],
                [{"name": "Triagem"}],
            ),
            (
                "out_4",
                doing,
                "Ajustar worker e fila de sincronizacao",
                "Objetivo estabilizar worker. Prazo definido. Responsavel Bruno. Proximo passo monitorar fila.",
                now - timedelta(days=2),
                [bruno],
                [{"name": "Infra"}],
            ),
            (
                "out_5",
                done,
                "Concluir checklist de release",
                "Objetivo fechar release. Criterio aceite completo. Responsavel Ana. Decisao registrada.",
                now + timedelta(days=2),
                [ana],
                [{"name": "Release"}],
            ),
        ]
        for card_id, board_list, title, description, due_at, assignees, labels in cards:
            card = Card.objects.create(
                trello_id=card_id,
                board=self.board,
                board_list=board_list,
                title=title,
                description=description,
                status=board_list.name,
                due_at=due_at,
                completed_at=now if board_list == done else None,
                last_activity_at=now - timedelta(days=8 if card_id in {"out_1", "out_4"} else 1),
                labels=labels,
                raw_json={"badges": {"checkItems": 4, "checkItemsCheck": 1 if card_id != "out_5" else 4}},
            )
            for assignee in assignees:
                card.assignees.add(assignee)
            if card_id in {"out_1", "out_2", "out_4"}:
                Action.objects.create(
                    trello_id=f"comment_{card_id}",
                    board=self.board,
                    member=ana,
                    action_type="commentCard",
                    occurred_at=now - timedelta(hours=2),
                    raw_json={
                        "data": {
                            "card": {"id": card_id},
                            "text": "Decisao: priorizar antes do proximo ciclo executivo.",
                        }
                    },
                )

    def test_json_contains_three_layers_tables_rankings_and_commercial_score(self) -> None:
        result = execute_report_query(ReportQueryPayload(board_id="output_board", use_cache=False))

        self.assertIn("report_output", result)
        self.assertIn("1_executive_brief", result["report_output"]["layers"])
        self.assertEqual(len(result["executive_brief"]["kpis_principais"]), 5)
        self.assertGreaterEqual(result["commercial_report_score"]["score"], 95)

        for key in ("kpis_principais", "top_categorias", "top_membros", "gargalos", "decisoes"):
            self.assertTrue(result["executive_tables"][key], key)
        for key in (
            "top_10_categories",
            "top_10_members",
            "top_10_critical_cards",
            "top_10_causes",
            "top_10_risks",
            "top_10_opportunities",
        ):
            self.assertIn(key, result["rankings"])

        decisions = result["executive_tables"]["decisoes"]
        self.assertTrue(decisions)
        self.assertTrue(all(item["evidencia"] for item in decisions))
        self.assertTrue(result["analytical_appendix"]["dados_por_card"])
        self.assertTrue(result["analytical_appendix"]["evidencias"])

    def test_markdown_contains_index_tables_rankings_and_appendix(self) -> None:
        result = execute_report_query(
            ReportQueryPayload(
                board_id="output_board",
                export_format=ExportFormat.MARKDOWN,
                use_cache=False,
            )
        )
        content = base64.b64decode(result["export"]["content_base64"]).decode("utf-8-sig")

        self.assertIn("## Índice", content)
        self.assertIn("### Tabela 1", content)
        self.assertIn("### Tabela 5", content)
        self.assertIn("## Rankings", content)
        self.assertIn("## Anexo Analítico", content)

    def test_pdf_declares_cover_and_kpi_contract(self) -> None:
        result = execute_report_query(
            ReportQueryPayload(board_id="output_board", export_format=ExportFormat.PDF, use_cache=False)
        )
        export = result["export"]

        self.assertEqual(export["content_type"], "application/pdf")
        self.assertTrue(export["visual_contract"]["cover"])
        self.assertTrue(export["visual_contract"]["kpi_cards"])
        self.assertIn("Capa", export["sections"])
        self.assertIn("KPIs", export["sections"])

    def test_pptx_outline_contains_mandatory_boardroom_slides(self) -> None:
        result = execute_report_query(
            ReportQueryPayload(board_id="output_board", export_format=ExportFormat.PPTX, use_cache=False)
        )
        outline = json.loads(base64.b64decode(result["export"]["content_base64"]).decode("utf-8-sig"))
        titles = [slide["title"] for slide in outline["slides"]]

        for title in (
            "Capa",
            "Executive Brief",
            "Scorecard Executivo",
            "Top 3 Drivers",
            "Riscos se Nada Mudar",
            "Gargalos",
            "Decisões recomendadas",
            "Plano de Ação",
            "Anexo Analítico",
        ):
            self.assertIn(title, titles)
