from datetime import datetime
from typing import Any

from django.utils.dateparse import parse_datetime

from apps.integrations.core.canonical import CanonicalTask

PROVIDER = "trello"


def parse_trello_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return parse_datetime(value.replace("Z", "+00:00"))


def map_board_to_project(board: dict[str, Any]) -> dict[str, Any]:
    """Board → canonical project representation."""
    return {
        "id": board["id"],
        "name": board.get("name") or "",
        "url": board.get("url") or "",
        "closed": bool(board.get("closed")),
        "workspace_id": board.get("idOrganization") or "",
    }


def map_list_to_status(list_item: dict[str, Any]) -> str:
    """List → status label (column name)."""
    return (list_item.get("name") or "").strip()


def map_card_to_task(
    card: dict[str, Any],
    *,
    project: dict[str, Any],
    list_by_id: dict[str, dict[str, Any]],
    workspace_id: str = "",
) -> CanonicalTask:
    """Card → canonical task."""
    list_id = card.get("idList", "")
    list_item = list_by_id.get(list_id, {})
    status = map_list_to_status(list_item) if list_item else ""

    due_raw = card.get("due")
    due_date = parse_trello_datetime(due_raw) if due_raw else None

    return CanonicalTask(
        source_provider=PROVIDER,
        source_id=card["id"],
        title=(card.get("name") or "").strip() or "(sem título)",
        status=status,
        due_date=due_date,
        project_id=project["id"],
        metadata={
            "project_name": project.get("name") or "",
            "project_url": project.get("url") or "",
            "workspace_id": workspace_id or project.get("workspace_id") or "",
            "list_id": list_id,
            "list_name": status,
            "closed": bool(card.get("closed")),
            "due_complete": bool(card.get("dueComplete")),
            "url": card.get("url") or card.get("shortUrl") or "",
            "labels": [
                {"id": label.get("id", ""), "name": label.get("name", ""), "color": label.get("color", "")}
                for label in (card.get("labels") or [])
            ],
        },
    )


def map_trello_payload(
    raw_payload: dict[str, Any],
    *,
    workspace_id: str = "",
) -> list[CanonicalTask]:
    """Map a full Trello fetch payload (board + lists + cards) to canonical tasks."""
    board = raw_payload["board"]
    project = map_board_to_project(board)
    resolved_workspace = workspace_id or project.get("workspace_id") or ""

    list_by_id: dict[str, dict[str, Any]] = {
        item["id"]: item for item in raw_payload.get("lists", [])
    }

    return [
        map_card_to_task(
            card,
            project=project,
            list_by_id=list_by_id,
            workspace_id=resolved_workspace,
        )
        for card in raw_payload.get("cards", [])
    ]
