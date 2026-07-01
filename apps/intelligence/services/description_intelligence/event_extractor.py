from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from django.utils import timezone

from apps.intelligence.domain.events import TimelineEventType
from apps.intelligence.models import TimelineEvent
from apps.intelligence.services.description_intelligence.parser import Evidence, ParsedDescription
from integrations.trello.models import Card


@dataclass
class ExtractedEvent:
    event_type: str
    label: str
    confidence: float
    evidence: list[Evidence] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "label": self.label,
            "confidence": self.confidence,
            "evidence": [item.to_dict() for item in self.evidence],
        }


EVENT_PATTERNS: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    ("PROBLEM_IDENTIFIED", "problema identificado", re.compile(r"\b(problema|falha|erro|incidente|causa)\b", re.I)),
    ("ANALYSIS_PERFORMED", "análise realizada", re.compile(r"\b(an[aá]lise|analisad|diagn[oó]stico|investigad|verificad)\b", re.I)),
    ("ACTION_EXECUTED", "ação executada", re.compile(r"\b(a[cç][aã]o|executad|corrigid|ajustad|alterad|realizad|aplicad)\b", re.I)),
    ("TEST_PERFORMED", "teste realizado", re.compile(r"\b(testad|validado|teste|valida[cç][aã]o)\b", re.I)),
    ("RESULT_RECORDED", "resultado", re.compile(r"\b(resultado|resolvid|normalizad|sucesso|sem erro)\b", re.I)),
    ("HOMOLOGATION", "homologação", re.compile(r"\b(homologa[cç][aã]o|homologad|hml)\b", re.I)),
    ("DEPLOYMENT", "implantação", re.compile(r"\b(implantad|deploy|publicad|release)\b", re.I)),
    ("ROLLBACK", "rollback", re.compile(r"\b(rollback|revers[aã]o|revertid)\b", re.I)),
    ("CLOSURE", "encerramento", re.compile(r"\b(encerrad|finalizad|conclu[ií]d)\b", re.I)),
)


def extract_events(parsed: ParsedDescription) -> list[ExtractedEvent]:
    """Detect operational events written in the description."""
    events: list[ExtractedEvent] = []
    for event_type, label, pattern in EVENT_PATTERNS:
        evidence = [line for line in parsed.lines if pattern.search(line.evidence)]
        if evidence:
            events.append(
                ExtractedEvent(
                    event_type=event_type,
                    label=label,
                    confidence=round(min(0.95, 0.55 + len(evidence[:3]) * 0.12), 2),
                    evidence=evidence[:5],
                )
            )
    return events


def persist_description_events(card: Card, events: list[ExtractedEvent]) -> int:
    """Persist description-derived events into Timeline without synthetic timestamps."""
    created = 0
    timestamp = card.last_activity_at or card.updated_at or timezone.now()
    for event in events:
        payload = event.to_dict()
        existing = TimelineEvent.objects.filter(
            board=card.board,
            card=card,
            source_action=None,
            event_type=TimelineEventType.UNKNOWN.value,
            payload_json__description_event_type=event.event_type,
        ).first()
        if existing:
            existing.event_timestamp = timestamp
            existing.actor = "description_intelligence"
            existing.payload_json = {
                **payload,
                "description_event_type": event.event_type,
                "source": "trello.card.description",
            }
            existing.save(update_fields=["event_timestamp", "actor", "payload_json", "updated_at"])
            continue

        TimelineEvent.objects.create(
            board=card.board,
            card=card,
            source_action=None,
            event_type=TimelineEventType.UNKNOWN.value,
            event_timestamp=timestamp,
            actor="description_intelligence",
            payload_json={
                **payload,
                "description_event_type": event.event_type,
                "source": "trello.card.description",
            },
        )
        created += 1
    return created
