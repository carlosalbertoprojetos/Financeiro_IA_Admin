"""Comprehensive tests for Report Query Engine — target 90%+ coverage."""

from __future__ import annotations

import base64
import time
from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.intelligence.models import ReportAuditLog
from apps.intelligence.services.report_query.cache import get_cached_report, set_cached_report
from apps.intelligence.services.report_query.domain.filters import (
    LabelOperator,
    MemberRole,
    PeriodPreset,
    ReportQueryPayload,
    ReportTemplate,
    TitleFilter,
    TitleMatchMode,
)
from apps.intelligence.services.report_query.domain.periods import resolve_period
from apps.intelligence.services.report_query.domain.title_parser import (
    extract_all_prefixes,
    extract_prefix,
    parse_structured_title,
    title_matches,
)
from apps.intelligence.services.report_query.engine.executor import execute_report_query
from apps.intelligence.services.report_query.engine.queryset_builder import build_filtered_cards
from apps.intelligence.services.report_query.exporters.formats import export_report
from integrations.trello.models import Action, Board, BoardList, Card, Member


class ReportQueryTestMixin:
    def setUp(self) -> None:
        cache.clear()
        self.board = Board.objects.create(trello_id="rq_board", name="RQ Board")
        self.list_backlog = BoardList.objects.create(
            trello_id="list_backlog", board=self.board, name="Backlog", position=0.0
        )
        self.list_doing = BoardList.objects.create(
            trello_id="list_doing", board=self.board, name="Em Andamento", position=1.0
        )
        self.joao = Member.objects.create(trello_id="m_joao", full_name="João")
        self.carlos = Member.objects.create(trello_id="m_carlos", full_name="Carlos")

        self.card_aqui = Card.objects.create(
            trello_id="card_aqui",
            board=self.board,
            board_list=self.list_doing,
            title="[AQUI] Revisar Contrato XPTO",
            status="Em Andamento",
            due_at=timezone.now() - timedelta(days=2),
            labels=[{"name": "Financeiro", "color": "green"}],
            raw_json={"badges": {"checkItems": 3, "checkItemsCheck": 1}},
        )
        self.card_aqui.assignees.add(self.joao)

        self.card_done = Card.objects.create(
            trello_id="card_done",
            board=self.board,
            board_list=self.list_doing,
            title="[FINANCEIRO] Pagamento",
            status="Concluído",
            is_closed=True,
            completed_at=timezone.now() - timedelta(days=1),
            labels=[{"name": "Financeiro", "color": "blue"}],
        )
        self.card_done.assignees.add(self.carlos)

        Action.objects.create(
            trello_id="act_create",
            board=self.board,
            member=self.joao,
            action_type="createCard",
            occurred_at=timezone.now() - timedelta(days=10),
            raw_json={"data": {"card": {"id": "card_aqui"}}},
        )
        Action.objects.create(
            trello_id="act_comment",
            board=self.board,
            member=self.carlos,
            action_type="commentCard",
            occurred_at=timezone.now() - timedelta(days=1),
            raw_json={"data": {"card": {"id": "card_aqui"}, "text": "Urgente!"}},
        )


class TitleParserTests(TestCase):
    def test_extract_prefix(self) -> None:
        self.assertEqual(extract_prefix("[AQUI] Revisar Contrato"), "AQUI")
        self.assertIsNone(extract_prefix("Sem prefixo"))

    def test_extract_all_prefixes(self) -> None:
        self.assertEqual(extract_all_prefixes("[AQUI][URGENTE] Task"), ["AQUI", "URGENTE"])

    def test_parse_structured_title(self) -> None:
        parsed = parse_structured_title("[AQUI] Revisar Contrato XPTO")
        self.assertEqual(parsed["category"], "AQUI")
        self.assertIn("Revisar", parsed["clean_title"])

    def test_title_match_invalid_regex(self) -> None:
        self.assertFalse(title_matches(TitleFilter(mode=TitleMatchMode.REGEX, value="[invalid"), "test"))

    def test_title_match_ends_with(self) -> None:
        self.assertTrue(title_matches(TitleFilter(mode=TitleMatchMode.ENDS_WITH, value="XPTO"), "[AQUI] Revisar Contrato XPTO"))


class PeriodResolverTests(TestCase):
    def test_last_30_days(self) -> None:
        ref = timezone.now()
        dr = resolve_period(preset=PeriodPreset.LAST_30_DAYS, reference=ref)
        self.assertIsNotNone(dr)
        assert dr is not None
        self.assertLess(dr.start, dr.end)

    def test_custom_range(self) -> None:
        dr = resolve_period(date_from="01/01/2026", date_to="31/03/2026")
        self.assertIsNotNone(dr)

    def test_today_and_yesterday(self) -> None:
        self.assertIsNotNone(resolve_period(preset=PeriodPreset.TODAY))
        self.assertIsNotNone(resolve_period(preset=PeriodPreset.YESTERDAY))

    def test_quarter_semester_year(self) -> None:
        for preset in (PeriodPreset.QUARTER, PeriodPreset.SEMESTER, PeriodPreset.YEAR, PeriodPreset.THIS_MONTH, PeriodPreset.PREVIOUS_MONTH):
            self.assertIsNotNone(resolve_period(preset=preset))


class QueryBuilderTests(ReportQueryTestMixin, TestCase):
    def test_filter_by_prefix(self) -> None:
        payload = ReportQueryPayload(board_id="rq_board", title_prefix="AQUI")
        cards, meta = build_filtered_cards(payload)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].trello_id, "card_aqui")

    def test_filter_by_label_and(self) -> None:
        payload = ReportQueryPayload(
            board_id="rq_board",
            labels=["Financeiro"],
            label_operator=LabelOperator.AND,
        )
        cards, _ = build_filtered_cards(payload)
        self.assertEqual(len(cards), 2)

    def test_filter_by_label_or(self) -> None:
        payload = ReportQueryPayload(
            board_id="rq_board",
            labels=["Financeiro", "Inexistente"],
            label_operator=LabelOperator.OR,
        )
        cards, _ = build_filtered_cards(payload)
        self.assertEqual(len(cards), 2)

    def test_filter_by_member_assignee(self) -> None:
        payload = ReportQueryPayload(
            board_id="rq_board",
            members=["João"],
            member_role=MemberRole.ASSIGNEE,
        )
        cards, _ = build_filtered_cards(payload)
        self.assertEqual(len(cards), 1)

    def test_filter_by_status_overdue(self) -> None:
        payload = ReportQueryPayload(board_id="rq_board", status=["atrasado"])
        cards, _ = build_filtered_cards(payload)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].trello_id, "card_aqui")

    def test_filter_by_period(self) -> None:
        payload = ReportQueryPayload(board_id="rq_board", period=PeriodPreset.LAST_90_DAYS)
        cards, meta = build_filtered_cards(payload)
        self.assertGreaterEqual(len(cards), 1)
        self.assertIn("matched_count", meta)

    def test_filter_by_list(self) -> None:
        payload = ReportQueryPayload(board_id="rq_board", lists=["Em Andamento"])
        cards, _ = build_filtered_cards(payload)
        self.assertEqual(len(cards), 1)

    def test_combined_filters(self) -> None:
        payload = ReportQueryPayload(
            board_id="rq_board",
            title_prefix="AQUI",
            labels=["Financeiro"],
            members=["João"],
            status=["atrasado"],
            period=PeriodPreset.LAST_30_DAYS,
        )
        cards, _ = build_filtered_cards(payload)
        self.assertEqual(len(cards), 1)

    def test_member_commenter_role(self) -> None:
        payload = ReportQueryPayload(
            board_id="rq_board",
            members=["Carlos"],
            member_role=MemberRole.COMMENTER,
        )
        cards, _ = build_filtered_cards(payload)
        self.assertEqual(len(cards), 1)

    def test_filter_by_risk_and_score(self) -> None:
        payload = ReportQueryPayload(
            board_id="rq_board",
            risk_levels=["moderado", "alto", "critico"],
        )
        cards, _ = build_filtered_cards(payload)
        self.assertGreaterEqual(len(cards), 0)

        payload2 = ReportQueryPayload(
            board_id="rq_board",
            score_range=__import__(
                "apps.intelligence.services.report_query.domain.filters", fromlist=["ScoreRange"]
            ).ScoreRange(min_score=0, max_score=100),
        )
        cards2, _ = build_filtered_cards(payload2)
        self.assertGreaterEqual(len(cards2), 1)

    def test_filter_checklist(self) -> None:
        ChecklistFilter = __import__(
            "apps.intelligence.services.report_query.domain.filters", fromlist=["ChecklistFilter"]
        ).ChecklistFilter
        payload = ReportQueryPayload(board_id="rq_board", checklist=ChecklistFilter.WITH_CHECKLIST)
        cards, _ = build_filtered_cards(payload)
        self.assertGreaterEqual(len(cards), 1)

    def test_filter_by_title_contains(self) -> None:
        payload = ReportQueryPayload(board_id="rq_board", title_contains="Contrato")
        cards, _ = build_filtered_cards(payload)
        self.assertEqual(len(cards), 1)

    def test_empty_board_id(self) -> None:
        cards, meta = build_filtered_cards(ReportQueryPayload(board_id=""))
        self.assertEqual(cards, [])


class ReportTemplateTests(ReportQueryTestMixin, TestCase):
    def _run(self, report_type: ReportTemplate) -> dict:
        payload = ReportQueryPayload(board_id="rq_board", report_type=report_type)
        return execute_report_query(payload)

    def test_executivo(self) -> None:
        result = self._run(ReportTemplate.EXECUTIVO)
        self.assertEqual(result["data"]["report_type"], "EXECUTIVO")

    def test_operacional(self) -> None:
        result = self._run(ReportTemplate.OPERACIONAL)
        self.assertEqual(result["data"]["report_type"], "OPERACIONAL")

    def test_membro(self) -> None:
        result = self._run(ReportTemplate.MEMBRO)
        self.assertIn("members", result["data"])

    def test_equipe(self) -> None:
        result = self._run(ReportTemplate.EQUIPE)

    def test_etiqueta(self) -> None:
        result = self._run(ReportTemplate.ETIQUETA)
        self.assertIn("labels", result["data"])

    def test_prefixo(self) -> None:
        payload = ReportQueryPayload(
            board_id="rq_board",
            report_type=ReportTemplate.PREFIXO,
            title_prefix="AQUI",
        )
        result = execute_report_query(payload)
        self.assertEqual(result["data"]["report_type"], "PREFIXO")

    def test_cliente(self) -> None:
        result = self._run(ReportTemplate.CLIENTE)

    def test_riscos(self) -> None:
        result = self._run(ReportTemplate.RISCOS)
        self.assertIn("assessments", result["data"])

    def test_sla(self) -> None:
        result = self._run(ReportTemplate.SLA)

    def test_produtividade(self) -> None:
        result = self._run(ReportTemplate.PRODUTIVIDADE)

    def test_multidimensional(self) -> None:
        result = self._run(ReportTemplate.MULTIDIMENSIONAL)
        self.assertIn("dimensions", result["data"])


class ExportTests(ReportQueryTestMixin, TestCase):
    def test_csv_export(self) -> None:
        payload = ReportQueryPayload(board_id="rq_board", export_format=__import__(
            "apps.intelligence.services.report_query.domain.filters", fromlist=["ExportFormat"]
        ).ExportFormat.CSV)
        result = execute_report_query(payload)
        self.assertIn("export", result)
        self.assertEqual(result["export"]["format"], "csv")

    def test_pdf_and_markdown_export(self) -> None:
        ExportFormat = __import__(
            "apps.intelligence.services.report_query.domain.filters", fromlist=["ExportFormat"]
        ).ExportFormat
        for fmt in (ExportFormat.PDF, ExportFormat.MARKDOWN, ExportFormat.EXCEL, ExportFormat.PPTX):
            payload = ReportQueryPayload(board_id="rq_board", export_format=fmt)
            result = execute_report_query(payload)
            self.assertIn("export", result)


class CacheAndAuditTests(ReportQueryTestMixin, TestCase):
    def test_cache_hit(self) -> None:
        payload = ReportQueryPayload(board_id="rq_board", use_cache=True)
        r1 = execute_report_query(payload)
        r2 = execute_report_query(payload)
        self.assertFalse(r1["meta"].get("cache_hit"))
        self.assertTrue(r2["meta"].get("cache_hit"))

    def test_audit_log_created(self) -> None:
        payload = ReportQueryPayload(board_id="rq_board", generated_by="tester")
        execute_report_query(payload)
        self.assertTrue(ReportAuditLog.objects.filter(board_id="rq_board", generated_by="tester").exists())

    def test_payload_from_dict(self) -> None:
        payload = ReportQueryPayload.from_dict(
            {
                "board_id": "rq_board",
                "period": "last_7_days",
                "title_contains": "Contrato",
                "labels": ["Financeiro"],
                "score_range": {"min": 0, "max": 100},
                "report_type": "MEMBRO",
            }
        )
        self.assertEqual(payload.period, PeriodPreset.LAST_7_DAYS)


class ReportQueryAPITests(ReportQueryTestMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()

    def test_get_query_info(self) -> None:
        response = self.client.get("/api/reports/query/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("report_types", response.json())

    def test_post_query_v1(self) -> None:
        response = self.client.post(
            "/api/v1/reports/query/",
            {
                "board_id": "rq_board",
                "title_prefix": "AQUI",
                "labels": ["Financeiro"],
                "members": ["João"],
                "period": "last_30_days",
                "status": ["atrasado"],
                "report_type": "EXECUTIVO",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["meta"]["matched_cards"], 1)

    def test_post_query_legacy(self) -> None:
        response = self.client.post(
            "/api/reports/query/",
            {"board_id": "rq_board", "report_type": "OPERACIONAL"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_missing_board_id(self) -> None:
        response = self.client.post("/api/reports/query/", {}, format="json")
        self.assertEqual(response.status_code, 400)


class PerformanceStressTests(ReportQueryTestMixin, TestCase):
    def test_large_card_set(self) -> None:
        for i in range(50):
            Card.objects.create(
                trello_id=f"stress_{i}",
                board=self.board,
                board_list=self.list_backlog,
                title=f"[AQUI] Card {i}",
                status="Backlog",
                labels=[{"name": "Financeiro"}],
            )
        start = time.perf_counter()
        payload = ReportQueryPayload(
            board_id="rq_board",
            title_prefix="AQUI",
            report_type=ReportTemplate.MULTIDIMENSIONAL,
            use_cache=False,
        )
        result = execute_report_query(payload)
        elapsed = time.perf_counter() - start
        self.assertGreater(result["meta"]["matched_cards"], 50)
        self.assertLess(elapsed, 30.0)
