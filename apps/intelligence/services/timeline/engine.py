"""Map Trello actions to canonical timeline events and persist them."""

from __future__ import annotations

import logging
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.intelligence.domain.events import TRELLO_ACTION_MAP, TimelineEventType
from apps.intelligence.models import TimelineEvent
from integrations.trello.models import Action, Board, Card

logger = logging.getLogger(__name__)

CRITICAL_EVENT_TYPES = frozenset(
    {
        TimelineEventType.BLOCKER_REGISTERED.value,
        TimelineEventType.CARD_REOPENED.value,
        TimelineEventType.DUE_DATE_CHANGED.value,
    }
)


def build_timeline_events_for_board(board: Board | str) -> int:
    """Build or update timeline events from Trello actions for a board."""
    if isinstance(board, str):
        board = Board.objects.get(trello_id=board)

    actions = Action.objects.filter(board=board).select_related("member").order_by("occurred_at")
    created = 0

    with transaction.atomic():
        for action in actions:
            created += _persist_events_for_action(action)

    logger.info("Built %s timeline events for board %s", created, board.trello_id)
    return created


def map_action_to_events(action: Action) -> list[dict[str, Any]]:
    """Convert a Trello action into one or more timeline event payloads."""
    raw = action.raw_json or {}
    data = raw.get("data") or {}
    action_type = action.action_type
    actor = _resolve_actor(action)
    card = _resolve_card(action)
    card_id = card.pk if card else None
    base = {
        "board_id": action.board_id,
        "card_id": card_id,
        "source_action_id": action.pk,
        "event_timestamp": action.occurred_at,
        "actor": actor,
    }

    events: list[dict[str, Any]] = []

    if action_type == "updateCard":
        events.extend(_map_update_card(base, data, raw))
    elif action_type in TRELLO_ACTION_MAP:
        event_type = TRELLO_ACTION_MAP[action_type]
        if action_type == "updateCheckItemStateOnCard" and not _is_checkitem_complete(data):
            event_type = TimelineEventType.CHECKLIST_ITEM_COMPLETED
        events.append(
            {
                **base,
                "event_type": event_type.value,
                "payload_json": _build_payload(action_type, data, raw),
            }
        )
    elif action_type:
        events.append(
            {
                **base,
                "event_type": TimelineEventType.UNKNOWN.value,
                "payload_json": {"trello_type": action_type, "data": data},
            }
        )

    return events


def build_card_timeline(card: Card) -> list[dict[str, Any]]:
    """Return structured timeline entries for a card (chronological)."""
    events = TimelineEvent.objects.filter(card=card).order_by("event_timestamp")
    return [
        {
            "event_type": event.event_type,
            "event_timestamp": event.event_timestamp.isoformat(),
            "actor": event.actor,
            "description": _describe_event(event),
            "is_critical": event.event_type in CRITICAL_EVENT_TYPES,
            "payload": event.payload_json,
        }
        for event in events
    ]


def _persist_events_for_action(action: Action) -> int:
    created = 0
    for payload in map_action_to_events(action):
        _, was_created = TimelineEvent.objects.update_or_create(
            source_action_id=payload["source_action_id"],
            event_type=payload["event_type"],
            defaults={
                "board_id": payload["board_id"],
                "card_id": payload.get("card_id"),
                "event_timestamp": payload["event_timestamp"],
                "actor": payload.get("actor", ""),
                "payload_json": payload.get("payload_json", {}),
            },
        )
        if was_created:
            created += 1
    return created


def _map_update_card(
    base: dict[str, Any],
    data: dict[str, Any],
    raw: dict[str, Any],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    old = data.get("old") or {}
    card_data = data.get("card") or {}

    if "idList" in old:
        events.append(
            {
                **base,
                "event_type": TimelineEventType.CARD_MOVED.value,
                "payload_json": {
                    "from_list": old.get("idList"),
                    "to_list": card_data.get("idList"),
                    "list_after": (data.get("listAfter") or {}).get("name"),
                    "list_before": (data.get("listBefore") or {}).get("name"),
                },
            }
        )

    if "due" in old or "due" in card_data:
        events.append(
            {
                **base,
                "event_type": TimelineEventType.DUE_DATE_CHANGED.value,
                "payload_json": {
                    "old_due": old.get("due"),
                    "new_due": card_data.get("due"),
                },
            }
        )

    if old.get("closed") is False and card_data.get("closed") is True:
        events.append(
            {
                **base,
                "event_type": TimelineEventType.CARD_COMPLETED.value,
                "payload_json": {"closed": True},
            }
        )
    elif old.get("closed") is True and card_data.get("closed") is False:
        events.append(
            {
                **base,
                "event_type": TimelineEventType.CARD_REOPENED.value,
                "payload_json": {"reopened": True},
            }
        )

    if not events:
        events.append(
            {
                **base,
                "event_type": TimelineEventType.UNKNOWN.value,
                "payload_json": {"trello_type": "updateCard", "data": data},
            }
        )

    return events


def _build_payload(action_type: str, data: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {"trello_type": action_type}
    if action_type == "commentCard":
        payload["text"] = (data.get("text") or "")[:2000]
    elif action_type in ("addLabelToCard", "removeLabelFromCard"):
        payload["label"] = data.get("label") or {}
    elif action_type in ("addMemberToCard", "removeMemberFromCard"):
        payload["member"] = data.get("member") or {}
    elif action_type == "updateCheckItemStateOnCard":
        payload["checkitem"] = data.get("checkItem") or {}
    elif action_type == "createCard":
        payload["card"] = data.get("card") or {}
    return payload


def _resolve_actor(action: Action) -> str:
    if action.member:
        return action.member.full_name or action.member.username or action.member.trello_id
    member_creator = (action.raw_json or {}).get("memberCreator") or {}
    return member_creator.get("fullName") or member_creator.get("username") or ""


def _resolve_card(action: Action) -> Card | None:
    data = (action.raw_json or {}).get("data") or {}
    card_data = data.get("card") or {}
    card_id = card_data.get("id")
    if not card_id:
        return None
    return Card.objects.filter(trello_id=card_id, board_id=action.board_id).first()


def _is_checkitem_complete(data: dict[str, Any]) -> bool:
    checkitem = data.get("checkItem") or {}
    return checkitem.get("state") == "complete"


def _describe_event(event: TimelineEvent) -> str:
    payload = event.payload_json or {}
    event_type = event.event_type

    descriptions = {
        TimelineEventType.CARD_CREATED.value: "Card criado",
        TimelineEventType.CARD_MOVED.value: f"Movido para {payload.get('list_after', 'outra lista')}",
        TimelineEventType.CARD_ASSIGNED.value: "Responsável atribuído",
        TimelineEventType.CARD_UNASSIGNED.value: "Responsável removido",
        TimelineEventType.LABEL_ADDED.value: f"Etiqueta adicionada: {(payload.get('label') or {}).get('name', '')}",
        TimelineEventType.LABEL_REMOVED.value: f"Etiqueta removida: {(payload.get('label') or {}).get('name', '')}",
        TimelineEventType.COMMENT_ADDED.value: "Comentário adicionado",
        TimelineEventType.CHECKLIST_STARTED.value: "Checklist iniciado",
        TimelineEventType.CHECKLIST_COMPLETED.value: "Checklist concluído",
        TimelineEventType.CHECKLIST_ITEM_COMPLETED.value: "Item de checklist concluído",
        TimelineEventType.DUE_DATE_CHANGED.value: "Prazo alterado",
        TimelineEventType.CARD_COMPLETED.value: "Card entregue",
        TimelineEventType.CARD_REOPENED.value: "Card reaberto",
        TimelineEventType.ATTACHMENT_ADDED.value: "Anexo adicionado",
        TimelineEventType.BLOCKER_REGISTERED.value: "Bloqueio registrado",
    }
    base = descriptions.get(event_type, event_type.replace("_", " ").title())
    if event.actor:
        return f"{base} — {event.actor}"
    return base
