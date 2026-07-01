from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable

from apps.intelligence.services.description_intelligence.structured_sections import (
    StructuredDescriptionDict,
    compute_documentation_completeness,
    parse_structured_description,
)


@dataclass
class NormalizedTrelloCard:
    id: str
    name: str
    list_name: str
    created_at: datetime | None = None
    due_date: datetime | None = None
    completed_at: datetime | None = None
    labels: list[dict[str, str]] = field(default_factory=list)
    members: list[dict[str, str]] = field(default_factory=list)
    checklists: list[dict[str, Any]] = field(default_factory=list)
    checklist_total: int = 0
    checklist_completed: int = 0
    checklist_completion_percent: float | None = None
    comments_count: int = 0
    attachments_count: int = 0
    description_sections: StructuredDescriptionDict = field(default_factory=dict)
    links: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    risks_count: int = 0
    evidences_count: int = 0
    documentation_completeness_score: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "list_name": self.list_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "labels": self.labels,
            "members": self.members,
            "checklists": self.checklists,
            "checklist_total": self.checklist_total,
            "checklist_completed": self.checklist_completed,
            "checklist_completion_percent": self.checklist_completion_percent,
            "comments_count": self.comments_count,
            "attachments_count": self.attachments_count,
            "description_sections": self.description_sections,
            "links": self.links,
            "metrics": self.metrics,
            "risks_count": self.risks_count,
            "evidences_count": self.evidences_count,
            "documentation_completeness_score": self.documentation_completeness_score,
        }


def normalize_trello_card(card: Any, *, actions: Iterable[Any] | None = None) -> NormalizedTrelloCard:
    """Build a report-friendly Trello card shape without mutating existing models."""
    description = _value(card, "description", "") or ""
    raw_json = _value(card, "raw_json", {}) or {}
    description_sections = parse_structured_description(description)
    checklists = _extract_checklists(raw_json)
    checklist_total, checklist_completed = _checklist_counts(checklists, raw_json)
    members = _members(card)
    has_owner = bool(members)
    has_checklist = checklist_total > 0
    comments_count = _comments_count(card, actions)
    attachments_count = _attachments_count(raw_json)

    return NormalizedTrelloCard(
        id=str(_value(card, "trello_id", _value(card, "id", "")) or ""),
        name=str(_value(card, "title", _value(card, "name", "")) or ""),
        list_name=_list_name(card),
        created_at=_value(card, "created_at", None),
        due_date=_value(card, "due_at", _value(card, "due_date", None)),
        completed_at=_value(card, "completed_at", None),
        labels=_labels(_value(card, "labels", []) or []),
        members=members,
        checklists=checklists,
        checklist_total=checklist_total,
        checklist_completed=checklist_completed,
        checklist_completion_percent=_completion_percent(checklist_total, checklist_completed),
        comments_count=comments_count,
        attachments_count=attachments_count,
        description_sections=description_sections,
        links=description_sections["links"],
        metrics=description_sections["metricas"],
        risks_count=len(description_sections["riscos"]),
        evidences_count=len(description_sections["evidencias"]),
        documentation_completeness_score=compute_documentation_completeness(
            description_sections,
            has_checklist=has_checklist,
            has_owner=has_owner,
        ),
    )


def _value(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _list_name(card: Any) -> str:
    board_list = _value(card, "board_list", None)
    if board_list is not None:
        name = _value(board_list, "name", "")
        if name:
            return str(name)
    return str(_value(card, "status", _value(card, "list_name", "")) or "")


def _labels(labels: Iterable[Any]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for label in labels:
        normalized.append(
            {
                "id": str(_value(label, "id", "") or ""),
                "name": str(_value(label, "name", "") or ""),
                "color": str(_value(label, "color", "") or ""),
            }
        )
    return normalized


def _members(card: Any) -> list[dict[str, str]]:
    assignees = _value(card, "assignees", None)
    if assignees is None:
        raw_members = _value(card, "members", []) or []
        return [
            {
                "id": str(_value(member, "trello_id", _value(member, "id", "")) or ""),
                "name": str(_value(member, "full_name", _value(member, "name", "")) or ""),
            }
            for member in raw_members
        ]

    if hasattr(assignees, "all"):
        assignees = assignees.all()

    members: list[dict[str, str]] = []
    for member in assignees:
        members.append(
            {
                "id": str(_value(member, "trello_id", _value(member, "id", "")) or ""),
                "name": str(
                    _value(member, "full_name", None)
                    or _value(member, "username", None)
                    or _value(member, "name", "")
                    or ""
                ),
            }
        )
    return members


def _extract_checklists(raw_json: dict[str, Any]) -> list[dict[str, Any]]:
    checklists = raw_json.get("checklists") or []
    if isinstance(checklists, list) and checklists and isinstance(checklists[0], dict):
        return checklists

    badges = raw_json.get("badges") or {}
    total = int(badges.get("checkItems") or 0)
    completed = int(badges.get("checkItemsCheck") or 0)
    if total:
        return [
            {
                "name": "Checklist",
                "checkItems": [
                    {
                        "name": f"Item {index + 1}",
                        "state": "complete" if index < completed else "incomplete",
                    }
                    for index in range(total)
                ],
            }
        ]
    return []


def _checklist_counts(
    checklists: list[dict[str, Any]],
    raw_json: dict[str, Any],
) -> tuple[int, int]:
    if not checklists:
        badges = raw_json.get("badges") or {}
        return int(badges.get("checkItems") or 0), int(badges.get("checkItemsCheck") or 0)

    total = 0
    completed = 0
    for checklist in checklists:
        for item in checklist.get("checkItems") or []:
            total += 1
            if item.get("state") == "complete":
                completed += 1
    return total, completed


def _completion_percent(total: int, completed: int) -> float | None:
    if total <= 0:
        return None
    return round(completed / total * 100, 1)


def _comments_count(card: Any, actions: Iterable[Any] | None) -> int:
    if actions is None:
        return 0
    card_id = str(_value(card, "trello_id", _value(card, "id", "")) or "")
    total = 0
    for action in actions:
        action_type = _value(action, "action_type", _value(action, "type", ""))
        if action_type != "commentCard":
            continue
        raw_json = _value(action, "raw_json", action) or {}
        action_card = ((raw_json.get("data") or {}).get("card") or {}).get("id")
        if not action_card or action_card == card_id:
            total += 1
    return total


def _attachments_count(raw_json: dict[str, Any]) -> int:
    attachments = raw_json.get("attachments")
    if isinstance(attachments, list):
        return len(attachments)
    badges = raw_json.get("badges") or {}
    return int(badges.get("attachments") or 0)

