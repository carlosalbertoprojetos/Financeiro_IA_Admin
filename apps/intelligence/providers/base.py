"""WorkManagementProvider — provider-agnostic interface for work management platforms."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar


@dataclass
class ProviderBoard:
    external_id: str
    name: str
    description: str = ""
    url: str = ""


@dataclass
class ProviderCard:
    external_id: str
    board_id: str
    title: str
    description: str = ""
    status: str = ""
    assignee_ids: list[str] = field(default_factory=list)
    labels: list[dict[str, str]] = field(default_factory=list)
    due_at: datetime | None = None
    completed_at: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderEvent:
    external_id: str
    board_id: str
    card_id: str | None
    event_type: str
    occurred_at: datetime
    actor: str = ""
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderSyncResult:
    boards: int = 0
    cards: int = 0
    events: int = 0
    provider: str = ""


class WorkManagementProvider(ABC):
    """
    Abstract interface for work management platform integrations.

    Implementations: Trello, Jira, ClickUp, Asana, Monday, Notion, Planner.
    Intelligence layer consumes normalized Provider* dataclasses regardless of source.
    """

    provider: ClassVar[str]

    @abstractmethod
    def authenticate(self, credentials: dict[str, Any]) -> None:
        """Validate credentials."""

    @abstractmethod
    def list_boards(self) -> list[ProviderBoard]:
        """List available boards/projects."""

    @abstractmethod
    def fetch_cards(self, board_id: str) -> list[ProviderCard]:
        """Fetch all cards/tasks for a board."""

    @abstractmethod
    def fetch_events(self, board_id: str, *, since: datetime | None = None) -> list[ProviderEvent]:
        """Fetch activity/events for a board."""

    def sync_board(self, board_id: str) -> ProviderSyncResult:
        """Default sync: fetch cards and events."""
        self.fetch_cards(board_id)
        events = self.fetch_events(board_id)
        return ProviderSyncResult(
            boards=1,
            cards=len(self.fetch_cards(board_id)),
            events=len(events),
            provider=self.provider,
        )


_PROVIDER_REGISTRY: dict[str, type[WorkManagementProvider]] = {}


def register_provider(provider_cls: type[WorkManagementProvider]) -> type[WorkManagementProvider]:
    _PROVIDER_REGISTRY[provider_cls.provider] = provider_cls
    return provider_cls


def get_provider(name: str) -> type[WorkManagementProvider]:
    if name not in _PROVIDER_REGISTRY:
        raise KeyError(f"Provider '{name}' not registered")
    return _PROVIDER_REGISTRY[name]


def list_providers() -> list[str]:
    return list(_PROVIDER_REGISTRY.keys())
