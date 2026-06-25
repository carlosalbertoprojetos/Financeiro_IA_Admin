"""Comprehensive tests for EOR Intelligence Engine V2."""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.intelligence.domain.events import TimelineEventType
from apps.intelligence.models import CardEnrichment, KnowledgeBaseEntry, TimelineEvent
from apps.intelligence.providers.base import get_provider, list_providers
from apps.intelligence.services.bottleneck_detector.detector import detect_bottlenecks
from apps.intelligence.services.checklist.intelligence import analyze_checklists
from apps.intelligence.services.communication_analysis.analyzer import analyze_communication
from apps.intelligence.services.enrichment.engine import enrich_card
from apps.intelligence.services.kpi.engine import compute_board_kpis
from apps.intelligence.services.operational_score.scorer import compute_operational_score
from apps.intelligence.services.orchestrator import run_intelligence_pipeline
from apps.intelligence.services.predictive.engine import predict_card
from apps.intelligence.services.report_builder import build_executive_report
from apps.intelligence.services.risk_engine.scorer import assess_card_risk, assess_board_risk
from apps.intelligence.services.timeline.engine import (
    build_card_timeline,
    build_timeline_events_for_board,
    map_action_to_events,
)
from integrations.trello.models import Action, Board, BoardList, Card, Member


class IntelligenceTestMixin:
    def setUp(self) -> None:
        self.board = Board.objects.create(trello_id="board1", name="Test Board")
        self.board_list = BoardList.objects.create(
            trello_id="list1", board=self.board, name="Doing", position=1.0
        )
        self.member = Member.objects.create(trello_id="member1", full_name="Alice")
        self.card = Card.objects.create(
            trello_id="card1",
            board=self.board,
            board_list=self.board_list,
            title="Urgent production fix",
            description="Cliente: ACME\nProjeto: Migration",
            status="Doing",
            due_at=timezone.now() + timedelta(days=2),
            raw_json={
                "badges": {"checkItems": 4, "checkItemsCheck": 2},
            },
        )
        self.card.assignees.add(self.member)


class TimelineEngineTests(IntelligenceTestMixin, TestCase):
    def test_map_create_card_action(self) -> None:
        action = Action.objects.create(
            trello_id="action1",
            board=self.board,
            member=self.member,
            action_type="createCard",
            occurred_at=timezone.now(),
            raw_json={
                "type": "createCard",
                "data": {"card": {"id": "card1", "name": "Test"}},
                "memberCreator": {"fullName": "Alice"},
            },
        )
        events = map_action_to_events(action)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], TimelineEventType.CARD_CREATED.value)

    def test_map_update_card_move(self) -> None:
        action = Action.objects.create(
            trello_id="action2",
            board=self.board,
            action_type="updateCard",
            occurred_at=timezone.now(),
            raw_json={
                "type": "updateCard",
                "data": {
                    "old": {"idList": "list0"},
                    "card": {"id": "card1", "idList": "list1"},
                    "listBefore": {"name": "Backlog"},
                    "listAfter": {"name": "Doing"},
                },
            },
        )
        events = map_action_to_events(action)
        types = [e["event_type"] for e in events]
        self.assertIn(TimelineEventType.CARD_MOVED.value, types)

    def test_build_timeline_events(self) -> None:
        Action.objects.create(
            trello_id="action3",
            board=self.board,
            action_type="commentCard",
            occurred_at=timezone.now(),
            raw_json={
                "type": "commentCard",
                "data": {"card": {"id": "card1"}, "text": "Bloqueio encontrado"},
            },
        )
        count = build_timeline_events_for_board(self.board)
        self.assertGreaterEqual(count, 1)
        self.assertTrue(TimelineEvent.objects.filter(board=self.board).exists())

    def test_build_card_timeline(self) -> None:
        build_timeline_events_for_board(self.board)
        timeline = build_card_timeline(self.card)
        self.assertIsInstance(timeline, list)


class EnrichmentEngineTests(IntelligenceTestMixin, TestCase):
    def test_detect_high_priority(self) -> None:
        context = enrich_card(self.card, persist=True)
        self.assertEqual(context.priority, "ALTA")
        self.assertTrue(CardEnrichment.objects.filter(card=self.card).exists())

    def test_detect_area(self) -> None:
        context = enrich_card(self.card, persist=False)
        self.assertIn(context.client.lower(), "acme")


class CommunicationAnalyzerTests(IntelligenceTestMixin, TestCase):
    def test_analyze_comments(self) -> None:
        Action.objects.create(
            trello_id="comment1",
            board=self.board,
            action_type="commentCard",
            occurred_at=timezone.now(),
            raw_json={
                "data": {
                    "card": {"id": "card1"},
                    "text": "Decidimos seguir com a opção A. Risco de atraso identificado.",
                }
            },
        )
        analysis = analyze_communication(self.card)
        self.assertEqual(analysis.comment_count, 1)
        self.assertTrue(analysis.decisions or analysis.risks)


class ChecklistIntelligenceTests(IntelligenceTestMixin, TestCase):
    def test_checklist_from_badges(self) -> None:
        metrics = analyze_checklists(self.card)
        self.assertEqual(metrics.total_items, 4)
        self.assertEqual(metrics.completed_items, 2)
        self.assertEqual(metrics.completion_pct, 50.0)


class RiskEngineTests(IntelligenceTestMixin, TestCase):
    def test_assess_card_risk(self) -> None:
        self.card.due_at = timezone.now() - timedelta(days=3)
        self.card.save()
        assessment = assess_card_risk(self.card)
        self.assertGreater(assessment.score, 0)
        self.assertIn(assessment.level, ("Baixo", "Moderado", "Alto", "Crítico"))

    def test_assess_board_risk(self) -> None:
        result = assess_board_risk(board_trello_id="board1")
        self.assertEqual(result["total_cards"], 1)


class KPIEngineTests(IntelligenceTestMixin, TestCase):
    def test_compute_kpis(self) -> None:
        kpis = compute_board_kpis(board_trello_id="board1")
        self.assertIn("lead_time", kpis)
        self.assertIn("cycle_time", kpis)
        self.assertIn("throughput", kpis)


class BottleneckDetectorTests(IntelligenceTestMixin, TestCase):
    def test_detect_bottlenecks(self) -> None:
        result = detect_bottlenecks(board_trello_id="board1")
        self.assertIn("summary", result)
        self.assertIn("stagnant_cards", result)


class PredictiveEngineTests(IntelligenceTestMixin, TestCase):
    def test_predict_card(self) -> None:
        prediction = predict_card(self.card)
        self.assertGreaterEqual(prediction.delay_probability, 0)
        self.assertLessEqual(prediction.delay_probability, 1)


class OperationalScoreTests(IntelligenceTestMixin, TestCase):
    def test_compute_score(self) -> None:
        result = compute_operational_score(board_trello_id="board1")
        self.assertGreaterEqual(result.score, 0)
        self.assertLessEqual(result.score, 100)
        self.assertIn(result.level, ("Verde", "Amarelo", "Laranja", "Vermelho"))


class OrchestratorTests(IntelligenceTestMixin, TestCase):
    def test_run_pipeline(self) -> None:
        result = run_intelligence_pipeline("board1", use_ai=False)
        self.assertEqual(result["board_id"], "board1")
        self.assertIn("operational_score", result)
        self.assertIn("report", result)


class ReportBuilderTests(IntelligenceTestMixin, TestCase):
    def test_build_report(self) -> None:
        report = build_executive_report("board1", use_ai=False)
        self.assertEqual(report["meta"]["version"], "EOR_V2")
        self.assertIn("1_resumo_executivo", report)
        self.assertIn("13_score_operacional", report)


class ProviderTests(TestCase):
    def test_trello_provider_registered(self) -> None:
        self.assertIn("trello", list_providers())
        provider_cls = get_provider("trello")
        provider = provider_cls(client=object())  # type: ignore[arg-type]
        boards = provider.list_boards()
        self.assertIsInstance(boards, list)
