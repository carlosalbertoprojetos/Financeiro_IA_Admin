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


class ReportDiscoveryEngineTests(TestCase):
    def setUp(self) -> None:
        cache.clear()
        self.board = Board.objects.create(trello_id="discovery_board", name="Discovery Board")
        self.backlog = BoardList.objects.create(
            trello_id="discovery_backlog",
            board=self.board,
            name="Backlog",
            position=0,
        )
        self.doing = BoardList.objects.create(
            trello_id="discovery_doing",
            board=self.board,
            name="Em Andamento",
            position=1,
        )
        self.member = Member.objects.create(trello_id="disc_ana", full_name="Ana")

        now = timezone.now()
        for index in range(8):
            poor = index < 5
            card = Card.objects.create(
                trello_id=f"disc_card_{index}",
                board=self.board,
                board_list=self.doing if index < 6 else self.backlog,
                title=(
                    f"[URGENTE] Corrigir incidente sistema erp projeto alpha {index}"
                    if index < 5
                    else f"Manutencao preventiva sistema crm projeto beta {index}"
                ),
                description="" if poor else (
                    "Objetivo: manter rotina preventiva. Prazo definido. "
                    "Responsavel Ana. Proximo passo validar checklist."
                ),
                status="Em Andamento" if index < 6 else "Backlog",
                due_at=now - timedelta(days=1) if index < 4 else None,
                last_activity_at=now - timedelta(days=9) if index < 4 else now - timedelta(days=1),
                labels=[{"name": "Incidente" if index < 5 else "Preventiva"}],
                raw_json={"badges": {"checkItems": 2, "checkItemsCheck": 0 if poor else 2}},
            )
            if index >= 5:
                card.assignees.add(self.member)
            Card.objects.filter(pk=card.pk).update(
                created_at=now - timedelta(days=10 if index < 2 else 1),
                updated_at=now - timedelta(days=9 if index < 4 else 1),
            )
            if index in (0, 1, 2):
                Action.objects.create(
                    trello_id=f"disc_comment_{index}",
                    board=self.board,
                    member=self.member,
                    action_type="commentCard",
                    occurred_at=now - timedelta(hours=index + 1),
                    raw_json={
                        "data": {
                            "card": {"id": f"disc_card_{index}"},
                            "text": "Decisao: tratar incidente repetitivo no sistema erp.",
                        }
                    },
                )

    def test_discovery_returns_only_evidenced_items(self) -> None:
        result = execute_report_query(ReportQueryPayload(board_id="discovery_board", use_cache=False))
        discovery = result["discovery"]

        self.assertGreater(discovery["report_intelligence_score"]["score"], 0)
        self.assertTrue(discovery["executive_highlights"])
        for collection_name in ("anomalies", "patterns", "executive_highlights", "opportunities"):
            for item in discovery[collection_name]:
                self.assertTrue(item["evidence"], collection_name)

    def test_correlations_require_minimum_sample_and_include_limits(self) -> None:
        result = execute_report_query(ReportQueryPayload(board_id="discovery_board", use_cache=False))
        correlations = result["discovery"]["correlations"]

        self.assertTrue(correlations)
        for correlation in correlations:
            self.assertGreaterEqual(correlation["sample"], 4)
            self.assertIn("coefficient", correlation)
            self.assertTrue(correlation["evidence"])
            self.assertTrue(correlation["limitations"])

    def test_forecast_requires_observed_trend(self) -> None:
        result = execute_report_query(ReportQueryPayload(board_id="discovery_board", use_cache=False))
        forecast = result["discovery"]["what_happens_next"]

        self.assertTrue(forecast)
        for scenario in forecast:
            self.assertTrue(scenario["trend_observed"])
            self.assertTrue(scenario["basis"])
            self.assertGreater(scenario["confidence"], 0)

    def test_no_false_anomaly_for_clean_small_board(self) -> None:
        clean_board = Board.objects.create(trello_id="clean_discovery_board", name="Clean")
        clean_list = BoardList.objects.create(
            trello_id="clean_discovery_list",
            board=clean_board,
            name="Doing",
            position=0,
        )
        owner = Member.objects.create(trello_id="clean_owner", full_name="Bruna")
        for index in range(3):
            card = Card.objects.create(
                trello_id=f"clean_card_{index}",
                board=clean_board,
                board_list=clean_list,
                title=f"Manutencao preventiva documentada {index}",
                description=(
                    "Objetivo: executar rotina planejada. Prazo definido. "
                    "Responsavel Bruna. Proximo passo registrar validacao."
                ),
                status="Em Andamento",
                due_at=timezone.now() + timedelta(days=5),
                labels=[{"name": "Preventiva"}],
                raw_json={"badges": {"checkItems": 2, "checkItemsCheck": 2}},
            )
            card.assignees.add(owner)
            Action.objects.create(
                trello_id=f"clean_comment_{index}",
                board=clean_board,
                member=owner,
                action_type="commentCard",
                occurred_at=timezone.now(),
                raw_json={"data": {"card": {"id": f"clean_card_{index}"}, "text": "Decisao registrada."}},
            )

        result = execute_report_query(ReportQueryPayload(board_id="clean_discovery_board", use_cache=False))

        self.assertEqual(result["discovery"]["anomalies"], [])
        self.assertEqual(result["discovery"]["correlations"], [])

    def test_discovery_exports_are_present_in_markdown_and_pptx(self) -> None:
        markdown = execute_report_query(
            ReportQueryPayload(
                board_id="discovery_board",
                export_format=ExportFormat.MARKDOWN,
                use_cache=False,
            )
        )
        content = base64.b64decode(markdown["export"]["content_base64"]).decode("utf-8-sig")
        self.assertIn("O que merece atenção", content)
        self.assertIn("Descobertas", content)
        self.assertIn("Cenário provável", content)

        pptx = execute_report_query(
            ReportQueryPayload(
                board_id="discovery_board",
                export_format=ExportFormat.PPTX,
                use_cache=False,
            )
        )
        outline = json.loads(base64.b64decode(pptx["export"]["content_base64"]).decode("utf-8-sig"))
        self.assertIn("discovery", outline)
        self.assertIn("report_intelligence", outline)
        self.assertIn("Descobertas", [slide["title"] for slide in outline["slides"]])
