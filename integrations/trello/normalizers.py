from datetime import datetime
from typing import Any

from django.utils.dateparse import parse_datetime


def parse_trello_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return parse_datetime(value.replace("Z", "+00:00"))


def normalize_labels(raw_labels: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    if not raw_labels:
        return []

    return [
        {
            "id": label.get("id", ""),
            "name": label.get("name", ""),
            "color": label.get("color", ""),
        }
        for label in raw_labels
    ]


def card_to_fields(
    card: dict[str, Any],
    *,
    list_by_trello_id: dict[str, Any],
) -> dict[str, Any]:
    board_list = list_by_trello_id.get(card.get("idList", ""))
    status = board_list.name if board_list else ""

    due_at = parse_trello_datetime(card.get("due"))
    completed_at = due_at if card.get("dueComplete") else None

    return {
        "trello_id": card["id"],
        "board_list": board_list,
        "title": card.get("name", "").strip() or "(sem título)",
        "description": card.get("desc") or "",
        "status": status,
        "due_at": due_at,
        "completed_at": completed_at,
        "is_closed": bool(card.get("closed")),
        "is_removed": False,
        "labels": normalize_labels(card.get("labels")),
        "url": card.get("url") or card.get("shortUrl") or "",
        "position": card.get("pos"),
        "last_activity_at": parse_trello_datetime(card.get("dateLastActivity")),
        "raw_json": card,
    }


def board_state_json(board: Any) -> dict[str, Any]:
    return {
        "trello_id": board.trello_id,
        "name": board.name,
        "description": board.description,
        "url": board.url,
        "closed": board.closed,
        "last_synced_at": board.last_synced_at.isoformat() if board.last_synced_at else None,
    }


def list_state_json(board_list: Any) -> dict[str, Any]:
    return {
        "trello_id": board_list.trello_id,
        "board_trello_id": board_list.board.trello_id,
        "name": board_list.name,
        "position": board_list.position,
        "closed": board_list.closed,
    }


def member_state_json(member: Any) -> dict[str, Any]:
    return {
        "trello_id": member.trello_id,
        "username": member.username,
        "full_name": member.full_name,
    }


def card_state_json(card: Any) -> dict[str, Any]:
    return {
        "trello_id": card.trello_id,
        "board_trello_id": card.board.trello_id,
        "board_list_trello_id": card.board_list.trello_id if card.board_list else None,
        "title": card.title,
        "description": card.description,
        "status": card.status,
        "due_at": card.due_at.isoformat() if card.due_at else None,
        "completed_at": card.completed_at.isoformat() if card.completed_at else None,
        "is_closed": card.is_closed,
        "is_removed": card.is_removed,
        "labels": card.labels,
        "url": card.url,
        "position": card.position,
        "last_activity_at": card.last_activity_at.isoformat() if card.last_activity_at else None,
        "assignee_trello_ids": list(card.assignees.values_list("trello_id", flat=True)),
    }
