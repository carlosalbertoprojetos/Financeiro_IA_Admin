import logging
from dataclasses import dataclass, field
from typing import Any

from django.db import close_old_connections, transaction
from django.utils import timezone

from integrations.trello.client import TrelloClient
from integrations.trello.models import (
    Action,
    Board,
    BoardList,
    Card,
    CardStatusHistory,
    EntityHistory,
    Member,
    Snapshot,
)
from integrations.trello.normalizers import (
    board_state_json,
    card_state_json,
    card_to_fields,
    list_state_json,
    member_state_json,
    parse_trello_datetime,
)

logger = logging.getLogger(__name__)

ACTION_UPSERT_BATCH_SIZE = 500
CARD_UPSERT_BATCH_SIZE = 200


@dataclass
class SyncBoardResult:
    board_id: str
    board_name: str
    lists: int = 0
    members: int = 0
    cards: int = 0
    actions: int = 0
    removed_cards: int = 0
    status_history_entries: int = 0
    entity_history_entries: int = 0
    snapshot_created: bool = False
    synced_at: str = field(default_factory=lambda: timezone.now().isoformat())

    def as_dict(self) -> dict[str, Any]:
        return {
            "board_id": self.board_id,
            "board_name": self.board_name,
            "lists": self.lists,
            "members": self.members,
            "cards": self.cards,
            "actions": self.actions,
            "removed_cards": self.removed_cards,
            "status_history_entries": self.status_history_entries,
            "entity_history_entries": self.entity_history_entries,
            "snapshot_created": self.snapshot_created,
            "synced_at": self.synced_at,
        }


def sync_board(board_id: str, client: TrelloClient | None = None) -> SyncBoardResult:
    """
    Fetch Trello board data and persist entities with event-sourcing history.
    """
    trello = client or TrelloClient()

    board_payload = trello.get_board(board_id)
    lists_payload = trello.get_board_lists(board_id)
    cards_payload = trello.get_board_cards(board_id)
    members_payload = trello.get_board_members(board_id)
    actions_payload = trello.get_board_actions(board_id)

    status_history_count = 0
    entity_history_count = 0
    snapshot_created = False

    logger.info(
        "Persisting board %s: %d lists, %d cards, %d members, %d actions",
        board_id,
        len(lists_payload),
        len(cards_payload),
        len(members_payload),
        len(actions_payload),
    )

    with transaction.atomic():
        board, _, board_history = _upsert_board(board_payload)
        entity_history_count += board_history

        member_map, member_history = _upsert_members(members_payload, board)
        entity_history_count += member_history

        list_map, list_history = _upsert_lists(board, lists_payload)
        entity_history_count += list_history

    action_count = _upsert_actions(
        board,
        actions_payload,
        member_map,
        batch_size=ACTION_UPSERT_BATCH_SIZE,
    )

    card_count, removed_count, card_history, card_status_history = _upsert_cards(
        board,
        cards_payload,
        list_map,
        member_map,
        batch_size=CARD_UPSERT_BATCH_SIZE,
    )
    entity_history_count += card_history
    status_history_count += card_status_history

    with transaction.atomic():
        snapshot_created = _upsert_daily_snapshot(board, list_map, member_map, card_count)

    result = SyncBoardResult(
        board_id=board.trello_id,
        board_name=board.name,
        lists=len(list_map),
        members=len(member_map),
        cards=card_count,
        actions=action_count,
        removed_cards=removed_count,
        status_history_entries=status_history_count,
        entity_history_entries=entity_history_count,
        snapshot_created=snapshot_created,
    )

    logger.info(
        "Synced Trello board %s (%s): %s",
        board.trello_id,
        board.name,
        result.as_dict(),
    )

    try:
        from apps.intelligence.services.timeline.engine import build_timeline_events_for_board

        build_timeline_events_for_board(board)
    except Exception:
        logger.exception("Failed to build timeline events for board %s", board.trello_id)

    try:
        from apps.intelligence.services.pilot.config import is_pilot_board
        from apps.intelligence.services.pilot.decision_stream import run_decision_stream

        if is_pilot_board(board.trello_id):
            run_decision_stream(board.trello_id, trigger="sync", limit=15)
    except Exception:
        logger.exception("POCL decision stream failed after sync for board %s", board.trello_id)

    return result


def _upsert_board(board_payload: dict[str, Any]) -> tuple[Board, bool, int]:
    existing = Board.objects.filter(trello_id=board_payload["id"]).first()
    board, created = Board.objects.update_or_create(
        trello_id=board_payload["id"],
        defaults={
            "name": board_payload.get("name", ""),
            "description": board_payload.get("desc") or "",
            "url": board_payload.get("url") or "",
            "closed": bool(board_payload.get("closed")),
            "last_synced_at": timezone.now(),
        },
    )
    history_count = 0
    if created or (existing and _board_changed(existing, board_payload)):
        history_count = _record_entity_history(
            EntityHistory.EntityType.BOARD,
            board.trello_id,
            board,
            board_state_json(board),
        )
    return board, created, history_count


def _board_changed(existing: Board, board_payload: dict[str, Any]) -> bool:
    return (
        existing.name != (board_payload.get("name") or "")
        or existing.description != (board_payload.get("desc") or "")
        or existing.url != (board_payload.get("url") or "")
        or existing.closed != bool(board_payload.get("closed"))
    )


def _record_entity_history(
    entity_type: str,
    entity_trello_id: str,
    board: Board | None,
    state_json: dict[str, Any],
    *,
    source: str = EntityHistory.Source.SYNC,
    source_action: Action | None = None,
) -> int:
    EntityHistory.objects.create(
        entity_type=entity_type,
        entity_trello_id=entity_trello_id,
        board=board,
        state_json=state_json,
        effective_at=timezone.now(),
        source=source,
        source_action=source_action,
    )
    return 1


def _upsert_members(
    members_payload: list[dict[str, Any]],
    board: Board,
) -> tuple[dict[str, Member], int]:
    member_map: dict[str, Member] = {}
    history_count = 0

    for payload in members_payload:
        existing = Member.objects.filter(trello_id=payload["id"]).first()
        member, created = Member.objects.update_or_create(
            trello_id=payload["id"],
            defaults={
                "username": payload.get("username") or "",
                "full_name": payload.get("fullName") or "",
            },
        )
        member_map[payload["id"]] = member

        if created or (existing and _member_changed(existing, payload)):
            history_count += _record_entity_history(
                EntityHistory.EntityType.MEMBER,
                member.trello_id,
                board,
                member_state_json(member),
            )

    return member_map, history_count


def _member_changed(existing: Member, payload: dict[str, Any]) -> bool:
    return (
        existing.username != (payload.get("username") or "")
        or existing.full_name != (payload.get("fullName") or "")
    )


def _upsert_lists(
    board: Board,
    lists_payload: list[dict[str, Any]],
) -> tuple[dict[str, BoardList], int]:
    list_map: dict[str, BoardList] = {}
    history_count = 0

    for payload in lists_payload:
        existing = BoardList.objects.filter(trello_id=payload["id"]).first()
        board_list, created = BoardList.objects.update_or_create(
            trello_id=payload["id"],
            defaults={
                "board": board,
                "name": payload.get("name", ""),
                "position": payload.get("pos") or 0,
                "closed": bool(payload.get("closed")),
            },
        )
        list_map[payload["id"]] = board_list

        if created or (existing and _list_changed(existing, payload)):
            history_count += _record_entity_history(
                EntityHistory.EntityType.LIST,
                board_list.trello_id,
                board,
                list_state_json(board_list),
            )

    return list_map, history_count


def _list_changed(existing: BoardList, payload: dict[str, Any]) -> bool:
    return (
        existing.name != (payload.get("name") or "")
        or existing.position != (payload.get("pos") or 0)
        or existing.closed != bool(payload.get("closed"))
    )


def _upsert_cards(
    board: Board,
    cards_payload: list[dict[str, Any]],
    list_map: dict[str, BoardList],
    member_map: dict[str, Member],
    *,
    batch_size: int = CARD_UPSERT_BATCH_SIZE,
) -> tuple[int, int, int, int]:
    synced_trello_ids: set[str] = set()
    entity_history_count = 0
    status_history_count = 0

    for batch_start in range(0, len(cards_payload), batch_size):
        batch = cards_payload[batch_start : batch_start + batch_size]
        with transaction.atomic():
            for card_payload in batch:
                fields = card_to_fields(card_payload, list_by_trello_id=list_map)
                assignee_ids = card_payload.get("idMembers") or []
                assignees = [
                    member_map[member_id] for member_id in assignee_ids if member_id in member_map
                ]

                existing = Card.objects.filter(trello_id=fields["trello_id"]).first()
                previous_status = existing.status if existing else None
                previous_list_id = existing.board_list_id if existing else None

                card, created = Card.objects.update_or_create(
                    trello_id=fields["trello_id"],
                    defaults={
                        "board": board,
                        "board_list": fields["board_list"],
                        "title": fields["title"],
                        "description": fields["description"],
                        "status": fields["status"],
                        "due_at": fields["due_at"],
                        "completed_at": fields["completed_at"],
                        "is_closed": fields["is_closed"],
                        "is_removed": False,
                        "labels": fields["labels"],
                        "url": fields["url"],
                        "position": fields["position"],
                        "last_activity_at": fields["last_activity_at"],
                        "raw_json": fields["raw_json"],
                    },
                )
                card.assignees.set(assignees)
                synced_trello_ids.add(fields["trello_id"])

                status_changed = (
                    created
                    or previous_status != card.status
                    or previous_list_id != card.board_list_id
                )
                if status_changed:
                    status_history_count += _record_card_status_history(
                        card, CardStatusHistory.Source.SYNC
                    )

                if created or (existing and _card_changed(existing, fields)):
                    entity_history_count += _record_entity_history(
                        EntityHistory.EntityType.CARD,
                        card.trello_id,
                        board,
                        card_state_json(card),
                    )

        if batch_start + batch_size < len(cards_payload):
            logger.info("Synced %d/%d cards", batch_start + len(batch), len(cards_payload))
            close_old_connections()

    with transaction.atomic():
        removed_count = (
            Card.objects.filter(board=board, is_removed=False)
            .exclude(trello_id__in=synced_trello_ids)
            .update(is_removed=True)
        )

    return len(synced_trello_ids), removed_count, entity_history_count, status_history_count


def _card_changed(existing: Card, fields: dict[str, Any]) -> bool:
    return (
        existing.title != fields["title"]
        or existing.description != fields["description"]
        or existing.status != fields["status"]
        or existing.board_list_id != (fields["board_list"].pk if fields["board_list"] else None)
        or existing.is_closed != fields["is_closed"]
        or existing.due_at != fields["due_at"]
        or existing.completed_at != fields["completed_at"]
        or existing.labels != fields["labels"]
        or existing.position != fields["position"]
    )


def _record_card_status_history(card: Card, source: str) -> int:
    board_list = card.board_list
    CardStatusHistory.objects.create(
        card=card,
        status=card.status,
        board_list=board_list,
        board_list_trello_id=board_list.trello_id if board_list else "",
        board_list_name=board_list.name if board_list else "",
        effective_at=card.last_activity_at or timezone.now(),
        source=source,
    )
    return 1


def _upsert_actions(
    board: Board,
    actions_payload: list[dict[str, Any]],
    member_map: dict[str, Member],
    *,
    batch_size: int = ACTION_UPSERT_BATCH_SIZE,
) -> int:
    count = 0
    total = len(actions_payload)

    for batch_start in range(0, total, batch_size):
        batch = actions_payload[batch_start : batch_start + batch_size]
        with transaction.atomic():
            for payload in batch:
                member_id = payload.get("idMemberCreator")
                member = member_map.get(member_id) if member_id else None

                _, created = Action.objects.update_or_create(
                    trello_id=payload["id"],
                    defaults={
                        "board": board,
                        "member": member,
                        "action_type": payload.get("type") or "unknown",
                        "raw_json": payload,
                        "occurred_at": parse_trello_datetime(payload.get("date")) or timezone.now(),
                    },
                )
                if created:
                    count += 1

        processed = batch_start + len(batch)
        if processed < total or processed == total:
            logger.info("Persisted %d/%d actions (%d new)", processed, total, count)
        close_old_connections()

    return count


def _upsert_daily_snapshot(
    board: Board,
    list_map: dict[str, BoardList],
    member_map: dict[str, Member],
    card_count: int,
) -> bool:
    today = timezone.localdate()
    cards = Card.objects.filter(board=board, is_removed=False).select_related("board_list")
    lists = list(list_map.values())
    members = list(member_map.values())
    total_actions = Action.objects.filter(board=board).count()

    state_json = {
        "board": board_state_json(board),
        "lists": [list_state_json(item) for item in lists],
        "members": [member_state_json(item) for item in members],
        "cards": [card_state_json(card) for card in cards],
        "captured_at": timezone.now().isoformat(),
    }

    _, created = Snapshot.objects.update_or_create(
        board=board,
        snapshot_date=today,
        defaults={
            "state_json": state_json,
            "card_count": card_count,
            "list_count": len(lists),
            "member_count": len(members),
            "action_count": total_actions,
        },
    )
    return created
