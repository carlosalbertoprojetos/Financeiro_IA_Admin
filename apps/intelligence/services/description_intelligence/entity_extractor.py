from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from apps.intelligence.services.description_intelligence.parser import Evidence, ParsedDescription


@dataclass
class ExtractedEntity:
    entity_type: str
    value: str
    confidence: float
    evidence: list[Evidence] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "value": self.value,
            "confidence": self.confidence,
            "evidence": [item.to_dict() for item in self.evidence],
        }


ENTITY_PATTERNS: dict[str, re.Pattern[str]] = {
    "ip": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "url": re.compile(r"https?://[^\s)>\]]+|www\.[^\s)>\]]+", re.I),
    "ticket": re.compile(r"\b(?:INC|REQ|CHG|TASK|BUG|SUP|TKT)[-_]?\d{3,}\b", re.I),
    "version": re.compile(r"\bv?\d+\.\d+(?:\.\d+)?(?:[-_][A-Za-z0-9.]+)?\b"),
    "host": re.compile(r"\b(?:srv|server|host|vm)[-_][A-Za-z0-9._-]+\b", re.I),
    "file": re.compile(r"\b[A-Za-z0-9_.-]+\.(?:log|sql|csv|xlsx|json|xml|yml|yaml|conf|ini|txt)\b", re.I),
    "database": re.compile(r"\b(?:postgres|postgresql|mysql|oracle|sql server|mongodb|redis|database|banco)\b", re.I),
    "protocol": re.compile(r"\b(?:https?|ssh|ftp|sftp|smtp|imap|pop3|tcp|udp|dns|vpn)\b", re.I),
    "environment": re.compile(r"\b(?:produção|prod|homologação|hml|staging|dev|desenvolvimento|qa)\b", re.I),
}

KEY_ENTITY_MAP = {
    "cliente": "cliente",
    "usuario": "usuario",
    "usuário": "usuario",
    "sistema": "sistema",
    "serviço": "servico",
    "servico": "servico",
    "equipamento": "equipamento",
    "ambiente": "environment",
    "projeto": "projeto",
    "area": "area",
    "área": "area",
    "departamento": "departamento",
    "software": "software",
}


def extract_entities(parsed: ParsedDescription) -> list[ExtractedEntity]:
    """Extract operational entities with source line evidence."""
    entities: list[ExtractedEntity] = []

    for entity_type, pattern in ENTITY_PATTERNS.items():
        for line in parsed.lines:
            for match in pattern.finditer(line.evidence):
                entities.append(
                    ExtractedEntity(
                        entity_type=entity_type,
                        value=match.group(0).strip(".,;"),
                        confidence=0.9,
                        evidence=[line],
                    )
                )

    for key, values in parsed.key_values.items():
        normalized = key.replace("_", " ")
        mapped = KEY_ENTITY_MAP.get(normalized)
        if mapped:
            for item in values:
                entities.append(
                    ExtractedEntity(
                        entity_type=mapped,
                        value=item.evidence,
                        confidence=0.95,
                        evidence=[item],
                    )
                )

    return _dedupe(entities)


def _dedupe(entities: list[ExtractedEntity]) -> list[ExtractedEntity]:
    seen: set[tuple[str, str]] = set()
    unique: list[ExtractedEntity] = []
    for entity in entities:
        key = (entity.entity_type, entity.value.lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(entity)
    return unique
