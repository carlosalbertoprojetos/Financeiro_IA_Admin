from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from apps.integrations.core.ingestion_state import IngestionCursor
from apps.integrations.trello.mapper import parse_trello_datetime


@dataclass
class IncrementalChangeStats:
    created: int = 0
    updated: int = 0
    moved: int = 0

    @property
    def total(self) -> int:
        return self.created + self.updated + self.moved

    def as_dict(self) -> dict[str, int]:
        return {
            "created": self.created,
            "updated": self.updated,
            "moved": self.moved,
            "total": self.total,
        }


@dataclass
class IncrementalCursorSnapshot:
    updated_since: datetime | None
    card_list_map: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_state(cls, state: IngestionCursor) -> IncrementalCursorSnapshot:
        since_raw = state.get("updated_since") or state.get("since")
        since_dt = parse_trello_datetime(since_raw) if since_raw else None
        raw_map = state.get("card_list_map") or {}
        card_list_map = {str(k): str(v) for k, v in raw_map.items()}
        return cls(updated_since=since_dt, card_list_map=card_list_map)


def filter_changed_cards(
    all_cards: list[dict[str, Any]],
    *,
    snapshot: IncrementalCursorSnapshot,
) -> tuple[list[dict[str, Any]], IncrementalChangeStats, str]:
    """
    Select cards changed since the last cursor.

    Trello has no native board cursor; we simulate incremental sync using:
    - updated_since + dateLastActivity (updates)
    - card_list_map membership (creates)
    - card_list_map idList diff (list moves)
    """
    if snapshot.updated_since is None:
        return list(all_cards), IncrementalChangeStats(created=len(all_cards)), "initial"

    changed: dict[str, dict[str, Any]] = {}
    stats = IncrementalChangeStats()

    for card in all_cards:
        card_id = card["id"]
        current_list = card.get("idList", "")
        previous_list = snapshot.card_list_map.get(card_id)
        activity = parse_trello_datetime(card.get("dateLastActivity"))

        is_created = previous_list is None
        is_updated = bool(activity and activity >= snapshot.updated_since)
        is_moved = (
            previous_list is not None
            and current_list
            and previous_list != current_list
        )

        if is_created:
            stats.created += 1
            changed[card_id] = card
            continue

        if is_moved:
            stats.moved += 1
            changed[card_id] = card
            continue

        if is_updated:
            stats.updated += 1
            changed[card_id] = card

    return list(changed.values()), stats, "incremental"


def build_next_cursor(
    *,
    board_id: str,
    all_cards: list[dict[str, Any]],
    synced_at: str,
    mode: str,
    change_stats: IncrementalChangeStats,
) -> dict[str, Any]:
    """Build cursor payload persisted as last_sync_cursor."""
    return {
        "updated_since": synced_at,
        "since": synced_at,  # backward compatibility
        "board_id": board_id,
        "mode": mode,
        "card_list_map": {card["id"]: card.get("idList", "") for card in all_cards},
        "changes_last_run": change_stats.as_dict(),
    }
