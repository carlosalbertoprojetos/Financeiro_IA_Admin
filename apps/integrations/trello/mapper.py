from datetime import datetime
from typing import Any

from django.utils.dateparse import parse_datetime

from apps.integrations.core.canonical import CanonicalTask
from apps.intelligence.services.description_intelligence.structured_sections import (
    compute_documentation_completeness,
    parse_structured_description,
)

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
    actions: list[dict[str, Any]] | None = None,
    member_by_id: dict[str, dict[str, Any]] | None = None,
    workspace_id: str = "",
) -> CanonicalTask:
    """Card → canonical task."""
    list_id = card.get("idList", "")
    list_item = list_by_id.get(list_id, {})
    status = map_list_to_status(list_item) if list_item else ""

    due_raw = card.get("due")
    due_date = parse_trello_datetime(due_raw) if due_raw else None
    description = card.get("desc") or ""
    description_sections = parse_structured_description(description)
    badges = card.get("badges") or {}
    checklist_total = int(badges.get("checkItems") or 0)
    checklist_completed = int(badges.get("checkItemsCheck") or 0)
    checklist_completion_percent = (
        round(checklist_completed / checklist_total * 100, 1)
        if checklist_total
        else None
    )
    labels = _map_labels(card.get("labels") or [])
    card_actions = actions or []
    members_lookup = member_by_id or {}
    assignees = _map_members(card.get("idMembers") or [], members_lookup)
    watchers = _map_members(
        card.get("idMembersWatching") or card.get("idMembersVoted") or [],
        members_lookup,
    )
    members = _dedupe_members([*assignees, *watchers])
    comments = _extract_comments(card_actions)
    action_history = _extract_history(card_actions)
    movements = _extract_movements(card_actions)
    checklists = _extract_checklists(card)
    attachments = _extract_attachments(card)
    dates = _extract_dates(card, due_date=due_date)
    evidence = _extract_evidence(description_sections, attachments)
    derived_fields = {
        "checklist_total": checklist_total,
        "checklist_completed": checklist_completed,
        "checklist_completion_percent": checklist_completion_percent,
        "comments_count": len(comments),
        "attachments_count": len(attachments),
        "actions_count": len(card_actions),
        "movements_count": len(movements),
        "labels_count": len(labels),
        "members_count": len(members),
        "assignees_count": len(assignees),
        "watchers_count": len(watchers),
        "risks_count": len(description_sections["riscos"]),
        "evidences_count": len(description_sections["evidencias"]),
        "documentation_completeness_score": compute_documentation_completeness(
            description_sections,
            has_checklist=checklist_total > 0,
            has_owner=bool(assignees),
        ),
        "closed": bool(card.get("closed")),
        "due_complete": bool(card.get("dueComplete")),
    }

    return CanonicalTask(
        source_provider=PROVIDER,
        source_id=card["id"],
        title=(card.get("name") or "").strip() or "(sem título)",
        status=status,
        due_date=due_date,
        project_id=project["id"],
        description=description,
        structured_description=description_sections,
        comments=comments,
        actions=action_history,
        history=action_history,
        movements=movements,
        checklists=checklists,
        attachments=attachments,
        members=members,
        assignees=assignees,
        watchers=watchers,
        labels=labels,
        dates=dates,
        derived_fields=derived_fields,
        evidence=evidence,
        raw={"card": card, "list": list_item, "project": project},
        metadata={
            "project_name": project.get("name") or "",
            "project_url": project.get("url") or "",
            "workspace_id": workspace_id or project.get("workspace_id") or "",
            "list_id": list_id,
            "list_name": status,
            "closed": bool(card.get("closed")),
            "due_complete": bool(card.get("dueComplete")),
            "url": card.get("url") or card.get("shortUrl") or "",
            "labels": labels,
            "description": description,
            "description_sections": description_sections,
            "structured_description": description_sections,
            "links": description_sections["links"],
            "metrics": description_sections["metricas"],
            "comments": comments,
            "actions": action_history,
            "history": action_history,
            "movements": movements,
            "checklists": checklists,
            "attachments": attachments,
            "members": members,
            "assignees": assignees,
            "watchers": watchers,
            "dates": dates,
            "derived_fields": derived_fields,
            "evidence": evidence,
            "risks_count": derived_fields["risks_count"],
            "evidences_count": derived_fields["evidences_count"],
            "checklist_total": derived_fields["checklist_total"],
            "checklist_completed": derived_fields["checklist_completed"],
            "checklist_completion_percent": derived_fields["checklist_completion_percent"],
            "documentation_completeness_score": derived_fields["documentation_completeness_score"],
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
    actions_by_card = _group_actions_by_card(raw_payload.get("actions") or [])
    member_by_id = {
        item["id"]: item
        for item in raw_payload.get("members", [])
        if item.get("id")
    }

    return [
        map_card_to_task(
            card,
            project=project,
            list_by_id=list_by_id,
            actions=actions_by_card.get(card.get("id", ""), []),
            member_by_id=member_by_id,
            workspace_id=resolved_workspace,
        )
        for card in raw_payload.get("cards", [])
    ]


def _map_labels(labels: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "id": str(label.get("id", "")),
            "name": str(label.get("name", "")),
            "color": str(label.get("color", "")),
        }
        for label in labels
    ]


def _map_members(
    member_ids: list[str],
    member_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    members = []
    for member_id in member_ids:
        payload = member_by_id.get(member_id, {})
        members.append(
            {
                "id": str(member_id),
                "username": str(payload.get("username", "")),
                "name": str(payload.get("fullName") or payload.get("name") or payload.get("username") or member_id),
            }
        )
    return members


def _dedupe_members(members: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    result = []
    for member in members:
        member_id = member.get("id", "")
        if member_id and member_id not in seen:
            seen.add(member_id)
            result.append(member)
    return result


def _group_actions_by_card(actions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for action in actions:
        card_id = (((action.get("data") or {}).get("card") or {}).get("id")) or ""
        if card_id:
            grouped.setdefault(card_id, []).append(action)
    return grouped


def _extract_comments(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    comments = []
    for action in actions:
        if action.get("type") != "commentCard":
            continue
        data = action.get("data") or {}
        comments.append(
            {
                "id": action.get("id", ""),
                "text": data.get("text", ""),
                "member_id": action.get("idMemberCreator", ""),
                "occurred_at": action.get("date"),
                "raw": action,
            }
        )
    return comments


def _extract_history(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": action.get("id", ""),
            "type": action.get("type") or "unknown",
            "member_id": action.get("idMemberCreator", ""),
            "occurred_at": action.get("date"),
            "data": action.get("data") or {},
            "raw": action,
        }
        for action in actions
    ]


def _extract_movements(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    movements = []
    for action in actions:
        data = action.get("data") or {}
        before = data.get("listBefore")
        after = data.get("listAfter")
        if not before or not after:
            continue
        movements.append(
            {
                "id": action.get("id", ""),
                "from_list": before,
                "to_list": after,
                "member_id": action.get("idMemberCreator", ""),
                "occurred_at": action.get("date"),
                "raw": action,
            }
        )
    return movements


def _extract_checklists(card: dict[str, Any]) -> list[dict[str, Any]]:
    checklists = card.get("checklists") or []
    if isinstance(checklists, list) and checklists and isinstance(checklists[0], dict):
        return checklists
    badges = card.get("badges") or {}
    total = int(badges.get("checkItems") or 0)
    completed = int(badges.get("checkItemsCheck") or 0)
    if not total:
        return []
    return [
        {
            "id": "",
            "name": "Checklist",
            "checkItems": [
                {
                    "id": "",
                    "name": f"Item {index + 1}",
                    "state": "complete" if index < completed else "incomplete",
                }
                for index in range(total)
            ],
            "source": "badges",
        }
    ]


def _extract_attachments(card: dict[str, Any]) -> list[dict[str, Any]]:
    attachments = card.get("attachments") or []
    if isinstance(attachments, list):
        return [
            {
                "id": attachment.get("id", ""),
                "name": attachment.get("name", ""),
                "url": attachment.get("url", ""),
                "mime_type": attachment.get("mimeType", ""),
                "date": attachment.get("date"),
                "raw": attachment,
            }
            for attachment in attachments
        ]
    return []


def _extract_dates(card: dict[str, Any], *, due_date: datetime | None) -> dict[str, Any]:
    return {
        "created_at": card.get("dateCreated") or card.get("created_at"),
        "due_at": due_date.isoformat() if due_date else None,
        "completed_at": card.get("completed_at"),
        "last_activity_at": card.get("dateLastActivity"),
        "start_at": card.get("start"),
        "due_complete": bool(card.get("dueComplete")),
    }


def _extract_evidence(
    description_sections: dict[str, Any],
    attachments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    evidence = [
        {"source": "description", "value": item}
        for item in description_sections.get("evidencias", [])
    ]
    evidence.extend(
        {
            "source": "attachment",
            "value": attachment.get("url") or attachment.get("name") or attachment.get("id"),
        }
        for attachment in attachments
        if attachment.get("url") or attachment.get("name") or attachment.get("id")
    )
    return evidence
