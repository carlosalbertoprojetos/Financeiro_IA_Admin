from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apps.intelligence.services.description_intelligence.event_extractor import ExtractedEvent
from apps.intelligence.services.description_intelligence.parser import ParsedDescription


@dataclass
class DescriptionQualityScore:
    score: int
    components: dict[str, int]
    missing: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {"score": self.score, "components": self.components, "missing": self.missing}


def compute_description_quality(
    parsed: ParsedDescription,
    *,
    entities_count: int = 0,
    events: list[ExtractedEvent] | None = None,
) -> DescriptionQualityScore:
    events = events or []
    text = parsed.normalized_text.strip()
    words = [w for w in text.split() if w.strip()]

    components = {
        "clareza": _points(bool(words), min(len(words), 80), 80),
        "objetividade": 15 if 20 <= len(words) <= 250 else 8 if words else 0,
        "completude": _completeness(parsed),
        "rastreabilidade": min(15, len(parsed.links) * 5 + entities_count * 2),
        "evidencias": min(15, len(parsed.tables) * 5 + len(parsed.code_blocks) * 3 + len(parsed.bullets) * 1),
        "detalhamento": min(15, len(parsed.lines) * 2),
        "resultado": 15 if any(e.event_type in ("RESULT_RECORDED", "CLOSURE") for e in events) else 0,
    }
    raw_score = sum(components.values())
    score = int(round(min(100, raw_score / 105 * 100)))
    missing = [name for name, value in components.items() if value == 0]
    return DescriptionQualityScore(score=score, components=components, missing=missing)


def _points(enabled: bool, current: int, target: int) -> int:
    if not enabled:
        return 0
    return min(15, int((current / target) * 15))


def _completeness(parsed: ParsedDescription) -> int:
    keys = set(parsed.key_values)
    signals = {
        "objetivo": any("objetivo" in key for key in keys),
        "problema": any("problema" in key for key in keys),
        "solucao": any(key in ("solucao", "solução", "acao", "ação") for key in keys),
        "resultado": any("resultado" in key for key in keys),
        "cliente": any("cliente" in key for key in keys),
    }
    return min(15, sum(3 for present in signals.values() if present))
