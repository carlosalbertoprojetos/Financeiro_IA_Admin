"""Unit tests for card metrics and filter edge cases."""

from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.intelligence.services.report_query.domain.filters import (
    ChecklistFilter,
    ScoreRange,
)
from apps.intelligence.services.report_query.domain.status_aliases import resolve_status_filter
from apps.intelligence.services.report_query.engine.card_metrics import (
    card_matches_checklist,
    card_matches_priority,
    card_matches_risk,
    card_matches_score,
    card_matches_status,
    card_member_matches,
    get_card_label_names,
)
from apps.intelligence.services.report_query.domain.filters import CardStatusFilter, MemberRole
from integrations.trello.models import Action, Board, BoardList, Card, Member


class CardMetricsTests(TestCase):
    def setUp(self) -> None:
        self.board = Board.objects.create(trello_id="cm_board", name="CM")
        self.list = BoardList.objects.create(trello_id="cm_list", board=self.board, name="Doing", position=1.0)
        self.member = Member.objects.create(trello_id="cm_m1", full_name="Ana")
        self.card = Card.objects.create(
            trello_id="cm_card",
            board=self.board,
            board_list=self.list,
            title="[URGENTE] Task crítica produção",
            status="Em Andamento",
            due_at=timezone.now() - timedelta(days=1),
            raw_json={"badges": {"checkItems": 2, "checkItemsCheck": 0}},
        )
        self.card.assignees.add(self.member)

    def test_status_filters(self) -> None:
        self.assertTrue(card_matches_status(self.card, CardStatusFilter.OVERDUE))
        self.assertTrue(card_matches_status(self.card, CardStatusFilter.IN_PROGRESS))
        self.assertTrue(card_matches_status(self.card, CardStatusFilter.OPEN))

    def test_priority_detection(self) -> None:
        self.assertTrue(card_matches_priority(self.card, "alta"))

    def test_checklist_filters(self) -> None:
        self.assertTrue(card_matches_checklist(self.card, ChecklistFilter.WITH_CHECKLIST))
        self.assertTrue(card_matches_checklist(self.card, ChecklistFilter.PENDING))
        self.assertFalse(card_matches_checklist(self.card, ChecklistFilter.WITHOUT_CHECKLIST))

    def test_risk_and_score(self) -> None:
        from apps.intelligence.services.risk_engine.scorer import assess_card_risk

        level = assess_card_risk(self.card).level
        self.assertIn(level, ("Baixo", "Moderado", "Alto", "Crítico"))
        self.assertTrue(card_matches_risk(self.card, level.lower().replace("í", "i")))
        score_range = ScoreRange(min_score=0, max_score=100)
        self.assertTrue(card_matches_score(self.card, score_range))

    def test_member_roles(self) -> None:
        Action.objects.create(
            trello_id="cm_a1",
            board=self.board,
            member=self.member,
            action_type="createCard",
            occurred_at=timezone.now(),
            raw_json={"data": {"card": {"id": "cm_card"}}},
        )
        Action.objects.create(
            trello_id="cm_a2",
            board=self.board,
            member=self.member,
            action_type="updateCard",
            occurred_at=timezone.now(),
            raw_json={"data": {"card": {"id": "cm_card"}}},
        )
        self.assertTrue(card_member_matches(self.card, ["Ana"], MemberRole.CREATOR))
        self.assertTrue(card_member_matches(self.card, ["Ana"], MemberRole.ASSIGNEE))
        self.assertTrue(card_member_matches(self.card, ["Ana"], MemberRole.LAST_EDITOR))
        self.assertTrue(card_member_matches(self.card, ["Ana"], MemberRole.PARTICIPANT))
        self.assertTrue(card_member_matches(self.card, ["Ana"], MemberRole.EXECUTOR))

    def test_label_names(self) -> None:
        self.card.labels = [{"name": "Urgente"}]
        self.assertEqual(get_card_label_names(self.card), ["Urgente"])

    def test_status_alias_resolver(self) -> None:
        self.assertEqual(resolve_status_filter("atrasado"), CardStatusFilter.OVERDUE)
        self.assertIsNone(resolve_status_filter("invalid_status_xyz"))

    def test_completed_card_status(self) -> None:
        self.card.is_closed = True
        self.card.status = "Concluído"
        self.assertTrue(card_matches_status(self.card, CardStatusFilter.COMPLETED))

    def test_checklist_completed(self) -> None:
        self.card.raw_json = {"badges": {"checkItems": 2, "checkItemsCheck": 2}}
        self.assertTrue(card_matches_checklist(self.card, ChecklistFilter.COMPLETED))
