from __future__ import annotations

import base64
import json
from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from apps.intelligence.services.report_query.domain.filters import ExportFormat, ReportQueryPayload
from apps.intelligence.services.report_query.engine.executor import execute_report_query
from apps.intelligence.services.report_query.engine.executive_story import build_executive_story
from integrations.trello.models import Action, Board, BoardList, Card, Member


class ExecutiveStoryEngineTests(TestCase):
    def setUp(self) -> None:
        cache.clear()
        self.board = Board.objects.create(trello_id="story_board", name="Story Board")
        self.doing = BoardList.objects.create(
            trello_id="story_doing",
            board=self.board,
            name="Em Andamento",
            position=1,
        )
        self.backlog = BoardList.objects.create(
            trello_id="story_backlog",
            board=self.board,
            name="Backlog",
            position=0,
        )
        self.member = Member.objects.create(trello_id="story_ana", full_name="Ana")
        now = timezone.now()

        for index in range(6):
            card = Card.objects.create(
                trello_id=f"story_card_{index}",
                board=self.board,
                board_list=self.doing if index < 4 else self.backlog,
                title=f"[URGENTE] Corrigir incidente sistema erp projeto alpha {index}",
                description="" if index < 4 else (
                    "Objetivo: estabilizar incidente. Prazo definido. "
                    "Responsavel Ana. Proximo passo validar correcao."
                ),
                status="Em Andamento",
                due_at=now - timedelta(days=1) if index < 3 else now + timedelta(days=3),
                last_activity_at=now - timedelta(days=8) if index < 3 else now,
                labels=[{"name": "Incidente"}],
                raw_json={"badges": {"checkItems": 2, "checkItemsCheck": 0 if index < 4 else 2}},
            )
            if index >= 4:
                card.assignees.add(self.member)
            if index < 3:
                Action.objects.create(
                    trello_id=f"story_comment_{index}",
                    board=self.board,
                    member=self.member,
                    action_type="commentCard",
                    occurred_at=now - timedelta(hours=index + 1),
                    raw_json={
                        "data": {
                            "card": {"id": f"story_card_{index}"},
                            "text": "Decisao: tratar incidente antes de novas demandas.",
                        }
                    },
                )

    def test_story_without_evidence_is_not_generated(self) -> None:
        story = build_executive_story(
            summary={},
            metrics={},
            analytical_enrichment={},
            executive_narrative={},
            discovery={},
            risks={},
            recommendations=[],
        )

        self.assertFalse(story["generated"])
        self.assertEqual(story["headline"], "")
        self.assertEqual(story["evidence_map"], [])
        self.assertEqual(story["executive_story_quality_score"]["score"], 0)

    def test_story_has_max_three_drivers_decisions_and_action_plan(self) -> None:
        result = execute_report_query(ReportQueryPayload(board_id="story_board", use_cache=False))
        story = result["executive_story"]

        self.assertTrue(story["generated"])
        self.assertLessEqual(len(story["key_drivers"]), 3)
        self.assertGreater(story["executive_story_quality_score"]["score"], 0)
        self.assertTrue(story["action_plan"])
        self.assertTrue(story["period_story"])
        for driver in story["key_drivers"]:
            self.assertTrue(driver["evidence"])
            self.assertTrue(driver["recommended_action"])

    def test_decision_ready_summary_has_evidence_and_urgency(self) -> None:
        result = execute_report_query(ReportQueryPayload(board_id="story_board", use_cache=False))
        decisions = result["executive_story"]["decision_ready_summary"]

        self.assertTrue(decisions)
        self.assertLessEqual(len(decisions), 3)
        for decision in decisions:
            self.assertTrue(decision["decision"])
            self.assertTrue(decision["reason"])
            self.assertTrue(decision["evidence"])
            self.assertTrue(decision["consequence_if_no_action"])
            self.assertTrue(decision["urgency"])
            self.assertTrue(decision["suggested_owner"])
            self.assertTrue(decision["suggested_deadline"])

    def test_story_exports_are_present_in_markdown_and_pptx(self) -> None:
        markdown = execute_report_query(
            ReportQueryPayload(
                board_id="story_board",
                export_format=ExportFormat.MARKDOWN,
                use_cache=False,
            )
        )
        content = base64.b64decode(markdown["export"]["content_base64"]).decode("utf-8-sig")
        self.assertIn("História Executiva", content)
        self.assertIn("Top 3 Drivers", content)
        self.assertIn("Decisões Prioritárias", content)

        pptx = execute_report_query(
            ReportQueryPayload(
                board_id="story_board",
                export_format=ExportFormat.PPTX,
                use_cache=False,
            )
        )
        outline = json.loads(base64.b64decode(pptx["export"]["content_base64"]).decode("utf-8-sig"))
        self.assertIn("executive_story", outline)
        self.assertEqual([slide["title"] for slide in outline["slides"][:8]], [
            "Executive Brief",
            "História Executiva",
            "Scorecard Executivo",
            "Benchmark Interno",
            "Top 3 Drivers",
            "Decisões Prioritárias",
            "Riscos se Nada Mudar",
            "Plano de Ação",
        ])
