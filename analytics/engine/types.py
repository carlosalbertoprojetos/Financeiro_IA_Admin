from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class StatusTransition:
    status: str
    effective_at: datetime
    list_position: float | None = None


@dataclass(frozen=True)
class CardRecord:
    id: str
    title: str = ""
    status: str = ""
    created_at: datetime | None = None
    completed_at: datetime | None = None
    due_at: datetime | None = None
    is_closed: bool = False
    is_removed: bool = False
    list_position: float | None = None
    assignee_ids: tuple[str, ...] = field(default_factory=tuple)
    assignee_names: tuple[str, ...] = field(default_factory=tuple)
    labels: tuple[dict[str, str], ...] = field(default_factory=tuple)
    status_history: tuple[StatusTransition, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ActionRecord:
    id: str
    action_type: str
    occurred_at: datetime
    card_id: str | None = None
    raw_json: dict[str, Any] = field(default_factory=dict)
