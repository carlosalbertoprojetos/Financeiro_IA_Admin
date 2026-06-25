"""Bottleneck detector — identifies congestion, stagnation, and overload."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any

from django.utils import timezone

from analytics.adapters import load_board_records


def detect_bottlenecks(
    *,
    board_trello_id: str | None = None,
    board_id: int | None = None,
    stagnation_days: float = 5.0,
    overload_threshold: int = 10,
) -> dict[str, Any]:
    """Detect operational bottlenecks across lists, cards, and assignees."""
    ref = timezone.now()
    cards, actions = load_board_records(
        board_trello_id=board_trello_id,
        board_id=board_id,
        reference_time=ref,
    )

    congested_lists = _detect_congested_lists(cards)
    stagnant_cards = _detect_stagnant_cards(cards, ref, stagnation_days)
    overloaded_assignees = _detect_overloaded_assignees(cards, overload_threshold)
    recurring_rework = _detect_recurring_rework(actions)
    repetitive_blockers = _detect_repetitive_blockers(actions)
    growing_queues = _detect_growing_queues(cards)

    return {
        "board_id": board_trello_id or board_id,
        "generated_at": ref.isoformat(),
        "congested_lists": congested_lists,
        "stagnant_cards": stagnant_cards,
        "overloaded_assignees": overloaded_assignees,
        "recurring_rework": recurring_rework,
        "repetitive_blockers": repetitive_blockers,
        "growing_queues": growing_queues,
        "summary": _build_summary(
            congested_lists,
            stagnant_cards,
            overloaded_assignees,
            recurring_rework,
        ),
    }


def _detect_congested_lists(cards: list) -> list[dict[str, Any]]:
    by_status: Counter[str] = Counter()
    for card in cards:
        if not card.is_closed and not card.is_removed:
            by_status[card.status or "unknown"] += 1

    if not by_status:
        return []

    avg = sum(by_status.values()) / len(by_status)
    threshold = max(avg * 1.5, 5)
    return [
        {"list": status, "wip": count, "severity": "high" if count > threshold * 1.5 else "medium"}
        for status, count in by_status.most_common()
        if count >= threshold
    ]


def _detect_stagnant_cards(cards: list, ref: datetime, days: float) -> list[dict[str, Any]]:
    cutoff = ref - timedelta(days=days)
    stagnant: list[dict[str, Any]] = []

    for card in cards:
        if card.is_closed or card.is_removed:
            continue
        last_move = _last_transition(card)
        if last_move and last_move < cutoff:
            stagnant.append(
                {
                    "card_id": card.id,
                    "title": card.title,
                    "status": card.status,
                    "stagnant_since": last_move.isoformat(),
                    "days_stagnant": round((ref - last_move).total_seconds() / 86400, 1),
                }
            )

    return sorted(stagnant, key=lambda x: x["days_stagnant"], reverse=True)[:20]


def _detect_overloaded_assignees(cards: list, threshold: int) -> list[dict[str, Any]]:
    load: Counter[str] = Counter()
    names: dict[str, str] = {}

    for card in cards:
        if card.is_closed or card.is_removed:
            continue
        for assignee_id, name in zip(card.assignee_ids, card.assignee_names):
            load[assignee_id] += 1
            names[assignee_id] = name

    return [
        {"assignee_id": aid, "name": names.get(aid, aid), "open_cards": count}
        for aid, count in load.most_common()
        if count >= threshold
    ]


def _detect_recurring_rework(actions: list) -> list[dict[str, Any]]:
    rework_by_card: Counter[str] = Counter()
    for action in actions:
        if action.action_type == "updateCard":
            old = (action.raw_json.get("data") or {}).get("old") or {}
            if "idList" in old:
                rework_by_card[action.card_id or "unknown"] += 1

    return [
        {"card_id": cid, "move_count": count}
        for cid, count in rework_by_card.most_common(10)
        if count >= 3 and cid != "unknown"
    ]


def _detect_repetitive_blockers(actions: list) -> list[dict[str, Any]]:
    blocker_comments: Counter[str] = Counter()
    keywords = ("bloqueio", "blocker", "impedimento", "blocked")

    for action in actions:
        if action.action_type != "commentCard":
            continue
        text = ((action.raw_json.get("data") or {}).get("text") or "").lower()
        if any(kw in text for kw in keywords):
            blocker_comments[action.card_id or "unknown"] += 1

    return [
        {"card_id": cid, "blocker_mentions": count}
        for cid, count in blocker_comments.most_common(10)
        if count >= 2 and cid != "unknown"
    ]


def _detect_growing_queues(cards: list) -> list[dict[str, Any]]:
    backlog_statuses = {"backlog", "todo", "to do", "a fazer", "pendente"}
    by_status: Counter[str] = Counter()
    for card in cards:
        if not card.is_closed and not card.is_removed:
            status = (card.status or "").lower()
            if status in backlog_statuses or "backlog" in status:
                by_status[card.status] += 1

    return [{"queue": s, "size": c} for s, c in by_status.most_common() if c >= 5]


def _last_transition(card) -> datetime | None:
    if card.status_history:
        return card.status_history[-1].effective_at
    return card.created_at


def _build_summary(
    lists: list,
    stagnant: list,
    overloaded: list,
    rework: list,
) -> str:
    parts: list[str] = []
    if lists:
        parts.append(f"{len(lists)} lista(s) congestionada(s)")
    if stagnant:
        parts.append(f"{len(stagnant)} card(s) estagnado(s)")
    if overloaded:
        parts.append(f"{len(overloaded)} responsável(is) sobrecarregado(s)")
    if rework:
        parts.append(f"{len(rework)} card(s) com retrabalho recorrente")
    return "; ".join(parts) if parts else "Nenhum gargalo crítico detectado."
