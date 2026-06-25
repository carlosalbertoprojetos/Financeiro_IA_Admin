"""
Real-world validation runner for Sprint 2.
Usage: python manage.py validate_eor --board-id BOARD_ID
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.intelligence.models import DecisionEffectivenessRecord, TimelineEvent
from apps.intelligence.services.organizational_learning.maturity.index import compute_eor_maturity_index
from apps.intelligence.services.organizational_learning.patterns.analyzer import analyze_action_patterns
from apps.intelligence.services.organizational_learning.playbooks.engine import generate_playbooks
from apps.intelligence.services.query_engine.runner import execute_eql_query
from apps.intelligence.services.semantic_layer.entity_mapper import map_card_to_entity
from integrations.trello.models import Card


@dataclass
class ValidationReport:
    board_id: str
    sync: dict[str, Any] = field(default_factory=dict)
    timeline: dict[str, Any] = field(default_factory=dict)
    semantic: dict[str, Any] = field(default_factory=dict)
    ole: dict[str, Any] = field(default_factory=dict)
    maturity: dict[str, Any] = field(default_factory=dict)
    query_sample: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Command(BaseCommand):
    help = "Validate EOR intelligence layers against real Trello board data."

    def add_arguments(self, parser):
        parser.add_argument("--board-id", type=str, required=True)
        parser.add_argument("--sync", action="store_true", help="Sync board from Trello before validation")
        parser.add_argument("--semantic-sample", type=int, default=100)
        parser.add_argument("--output", type=str, default="")

    def handle(self, *args, **options):
        board_id: str = options["board_id"]
        report = ValidationReport(board_id=board_id)

        if options["sync"]:
            from integrations.trello.exceptions import TrelloAPIError
            from integrations.trello.services.sync import sync_board

            try:
                result = sync_board(board_id)
                report.sync = result.as_dict()
            except TrelloAPIError as exc:
                raise CommandError(str(exc)) from exc
        else:
            report.sync = {"skipped": True, "board_id": board_id}

        cards_qs = Card.objects.filter(board__trello_id=board_id, is_removed=False)
        total_cards = cards_qs.count()
        if total_cards == 0:
            raise CommandError(f"No cards found for board {board_id}. Run with --sync first.")

        events = TimelineEvent.objects.filter(board__trello_id=board_id)
        report.timeline = {
            "total_events": events.count(),
            "event_types": list(events.values_list("event_type", flat=True).distinct()[:20]),
            "cards_with_events": events.values("card_id").distinct().count(),
            "date_range": _event_date_range(events),
        }

        sample_size = min(options["semantic_sample"], total_cards)
        sample_cards = list(cards_qs.select_related("board_list").prefetch_related("assignees")[:sample_size])
        classified = 0
        type_counts: dict[str, int] = {}
        for card in sample_cards:
            entity = map_card_to_entity(card, row={"risk_score": 0})
            classified += 1
            et = entity.entity_type.value
            type_counts[et] = type_counts.get(et, 0) + 1

        report.semantic = {
            "sample_size": sample_size,
            "classified": classified,
            "entity_type_distribution": type_counts,
            "classification_rate_pct": round((classified / sample_size) * 100, 1) if sample_size else 0,
        }

        patterns = analyze_action_patterns(board_id=board_id)
        playbooks = generate_playbooks(board_id=board_id, min_sample_size=3)
        report.ole = {
            "effectiveness_records": DecisionEffectivenessRecord.objects.filter(board_id=board_id).count(),
            "patterns": patterns,
            "playbooks_count": len(playbooks),
            "playbooks_approved": [p for p in playbooks if p.get("sample_size", 0) >= 3],
        }
        report.maturity = compute_eor_maturity_index(board_id=board_id)

        if total_cards > 0:
            try:
                q = "REPORT:\nTYPE = EXECUTIVE\nFILTER:\nPERIOD = LAST_30_DAYS\nLIMIT:\n10\n"
                result = execute_eql_query(q, board_id=board_id, use_cache=False)
                report.query_sample = {
                    "matched_cards": result.get("summary", {}).get("matched_cards", 0),
                    "has_decisions": bool(result.get("decisions")),
                    "trace_id": result.get("trace_id", ""),
                }
            except Exception as exc:
                report.query_sample = {"error": str(exc)}

        payload = report.to_dict()
        if options["output"]:
            with open(options["output"], "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, default=str)
            self.stdout.write(self.style.SUCCESS(f"Validation report written to {options['output']}"))
        else:
            self.stdout.write(json.dumps(payload, indent=2, default=str))


def _event_date_range(events) -> dict[str, str]:
    first = events.order_by("event_timestamp").first()
    last = events.order_by("-event_timestamp").first()
    return {
        "from": first.event_timestamp.isoformat() if first else "",
        "to": last.event_timestamp.isoformat() if last else "",
    }
