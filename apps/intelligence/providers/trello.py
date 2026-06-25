"""Trello WorkManagementProvider adapter."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from django.utils import timezone

from apps.intelligence.domain.events import TimelineEventType
from apps.intelligence.providers.base import (
    ProviderBoard,
    ProviderCard,
    ProviderEvent,
    WorkManagementProvider,
    register_provider,
)
from apps.intelligence.services.timeline.engine import map_action_to_events
from integrations.trello.client import TrelloClient as LegacyTrelloClient
from integrations.trello.models import Action, Board, Card
from integrations.trello.normalizers import parse_trello_datetime


@register_provider
class TrelloWorkManagementProvider(WorkManagementProvider):
    provider = "trello"

    def __init__(self, client: LegacyTrelloClient | None = None) -> None:
        self._client = client

    def _get_client(self) -> LegacyTrelloClient:
        if self._client is None:
            self._client = LegacyTrelloClient()
        return self._client

    def authenticate(self, credentials: dict[str, Any]) -> None:
        self._get_client().get_board(credentials.get("board_id", "test"))

    def list_boards(self) -> list[ProviderBoard]:
        return [
            ProviderBoard(
                external_id=b.trello_id,
                name=b.name,
                description=b.description,
                url=b.url,
            )
            for b in Board.objects.all()
        ]

    def fetch_cards(self, board_id: str) -> list[ProviderCard]:
        board = Board.objects.filter(trello_id=board_id).first()
        if board:
            return [self._card_from_orm(c) for c in board.cards.filter(is_removed=False)]
        payloads = self._get_client().get_board_cards(board_id)
        return [self._card_from_payload(p, board_id) for p in payloads]

    def fetch_events(self, board_id: str, *, since: datetime | None = None) -> list[ProviderEvent]:
        board = Board.objects.filter(trello_id=board_id).first()
        if board:
            actions = Action.objects.filter(board=board).select_related("member")
            if since:
                actions = actions.filter(occurred_at__gte=since)
            events: list[ProviderEvent] = []
            for action in actions:
                for payload in map_action_to_events(action):
                    events.append(
                        ProviderEvent(
                            external_id=f"{action.trello_id}:{payload['event_type']}",
                            board_id=board_id,
                            card_id=action.raw_json.get("data", {}).get("card", {}).get("id"),
                            event_type=payload["event_type"],
                            occurred_at=payload["event_timestamp"],
                            actor=payload.get("actor", ""),
                            payload=payload.get("payload_json", {}),
                        )
                    )
            return events

        actions_payload = self._get_client().get_board_actions(board_id)
        events = []
        for payload in actions_payload:
            occurred = parse_trello_datetime(payload.get("date")) or timezone.now()
            if since and occurred < since:
                continue
            action_type = payload.get("type", "unknown")
            event_type = TimelineEventType.UNKNOWN.value
            if action_type == "createCard":
                event_type = TimelineEventType.CARD_CREATED.value
            elif action_type == "commentCard":
                event_type = TimelineEventType.COMMENT_ADDED.value
            events.append(
                ProviderEvent(
                    external_id=payload["id"],
                    board_id=board_id,
                    card_id=(payload.get("data") or {}).get("card", {}).get("id"),
                    event_type=event_type,
                    occurred_at=occurred,
                    payload=payload,
                )
            )
        return events

    def _card_from_orm(self, card: Card) -> ProviderCard:
        return ProviderCard(
            external_id=card.trello_id,
            board_id=card.board.trello_id,
            title=card.title,
            description=card.description,
            status=card.status,
            assignee_ids=[m.trello_id for m in card.assignees.all()],
            labels=list(card.labels or []),
            due_at=card.due_at,
            completed_at=card.completed_at,
            raw=card.raw_json,
        )

    def _card_from_payload(self, payload: dict, board_id: str) -> ProviderCard:
        return ProviderCard(
            external_id=payload["id"],
            board_id=board_id,
            title=payload.get("name", ""),
            description=payload.get("desc", ""),
            status=(payload.get("list") or {}).get("name", ""),
            due_at=parse_trello_datetime(payload.get("due")),
            raw=payload,
        )
