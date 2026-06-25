"""Diagnose why report filters return zero cards."""

from __future__ import annotations

from collections import Counter
from typing import Any

from django.utils import timezone

from integrations.trello.models import Board, Card, Member


def diagnose_board_filters(board_trello_id: str) -> dict[str, Any]:
    board = Board.objects.filter(trello_id=board_trello_id).first()
    if not board:
        available = list(Board.objects.values_list("trello_id", "name")[:10])
        return {
            "error": f"Board '{board_trello_id}' not found in database.",
            "hint": "Run sync first. Available boards:",
            "available_boards": [{"id": bid, "name": name} for bid, name in available],
        }

    cards_qs = Card.objects.filter(board=board, is_removed=False)
    total = cards_qs.count()

    label_counter: Counter[str] = Counter()
    prefix_counter: Counter[str] = Counter()
    status_counter: Counter[str] = Counter()
    now = timezone.now()
    overdue = 0

    for card in cards_qs.only("title", "labels", "status", "due_at", "is_closed")[:2000]:
        for label in card.labels or []:
            name = label.get("name") or "(sem nome)"
            label_counter[name] += 1
        if card.title and "[" in card.title:
            prefix = card.title.split("]")[0] + "]"
            prefix_counter[prefix] += 1
        status_counter[card.status or "(vazio)"] += 1
        if card.due_at and card.due_at < now and not card.is_closed:
            overdue += 1

    members = (
        Member.objects.filter(cards__board=board)
        .distinct()
        .values_list("full_name", "username", flat=False)
    )

    return {
        "board_id": board.trello_id,
        "board_name": board.name,
        "total_cards": total,
        "overdue_cards": overdue,
        "top_labels": label_counter.most_common(15),
        "top_title_prefixes": prefix_counter.most_common(15),
        "top_statuses": status_counter.most_common(10),
        "members": [{"full_name": fn, "username": un} for fn, un in members[:30]],
        "tips": [
            "title_prefix must match brackets in title, e.g. [Financeiro] not Financeiro",
            "labels filter uses Trello label names, not title prefixes",
            "members supports partial match, e.g. Carlos matches Carlos_Alberto",
            "use --board-id with the trello_id stored after sync (see available_boards if missing)",
        ],
    }
