from datetime import datetime
from typing import Iterable

from django.utils import timezone

from analytics.engine.types import ActionRecord, CardRecord, StatusTransition
from integrations.trello.models import Action, Card


def card_to_record(card: Card) -> CardRecord:
    history = [
        StatusTransition(
            status=entry.status,
            effective_at=entry.effective_at,
            list_position=entry.board_list.position if entry.board_list else None,
        )
        for entry in card.status_history.select_related("board_list").order_by("effective_at")
    ]
    assignees = list(card.assignees.all())

    return CardRecord(
        id=card.trello_id,
        title=card.title,
        status=card.status,
        created_at=card.created_at,
        completed_at=card.completed_at,
        due_at=card.due_at,
        is_closed=card.is_closed,
        is_removed=card.is_removed,
        list_position=card.board_list.position if card.board_list else card.position,
        assignee_ids=tuple(member.trello_id for member in assignees),
        assignee_names=tuple(member.full_name or member.username or member.trello_id for member in assignees),
        labels=tuple(
            {
                "id": str(label.get("id", "")),
                "name": str(label.get("name", "")),
                "color": str(label.get("color", "")),
            }
            for label in (card.labels or [])
        ),
        status_history=tuple(history),
    )


def action_to_record(action: Action) -> ActionRecord:
    card_id = _extract_card_id_from_action(action)
    return ActionRecord(
        id=action.trello_id,
        action_type=action.action_type,
        occurred_at=action.occurred_at,
        card_id=card_id,
        raw_json=action.raw_json,
    )


def cards_to_records(cards: Iterable[Card]) -> list[CardRecord]:
    return [card_to_record(card) for card in cards]


def actions_to_records(actions: Iterable[Action]) -> list[ActionRecord]:
    return [action_to_record(action) for action in actions]


def load_board_records(
    *,
    board_trello_id: str | None = None,
    board_id: int | None = None,
    include_removed: bool = False,
    reference_time: datetime | None = None,
) -> tuple[list[CardRecord], list[ActionRecord]]:
    cards_qs = Card.objects.select_related("board_list").prefetch_related(
        "status_history__board_list",
        "assignees",
    )
    actions_qs = Action.objects.all()

    if board_trello_id:
        cards_qs = cards_qs.filter(board__trello_id=board_trello_id)
        actions_qs = actions_qs.filter(board__trello_id=board_trello_id)
    elif board_id:
        cards_qs = cards_qs.filter(board_id=board_id)
        actions_qs = actions_qs.filter(board_id=board_id)

    if not include_removed:
        cards_qs = cards_qs.filter(is_removed=False)

    cards = cards_to_records(cards_qs)
    actions = actions_to_records(actions_qs.order_by("occurred_at"))

    if reference_time is None:
        reference_time = timezone.now()

    return cards, actions


def _extract_card_id_from_action(action: Action) -> str | None:
    data = action.raw_json.get("data") or {}
    card = data.get("card") or {}
    return card.get("id")
