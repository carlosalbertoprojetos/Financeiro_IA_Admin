from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Evidence:
    source: str
    line: int
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        return {"source": self.source, "line": self.line, "evidence": self.evidence}


@dataclass
class ParsedDescription:
    raw_text: str
    normalized_text: str
    lines: list[Evidence] = field(default_factory=list)
    headings: list[Evidence] = field(default_factory=list)
    bullets: list[Evidence] = field(default_factory=list)
    links: list[Evidence] = field(default_factory=list)
    tables: list[Evidence] = field(default_factory=list)
    code_blocks: list[Evidence] = field(default_factory=list)
    key_values: dict[str, list[Evidence]] = field(default_factory=dict)
    sections: dict[str, list[Evidence]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
            "lines": [item.to_dict() for item in self.lines],
            "headings": [item.to_dict() for item in self.headings],
            "bullets": [item.to_dict() for item in self.bullets],
            "links": [item.to_dict() for item in self.links],
            "tables": [item.to_dict() for item in self.tables],
            "code_blocks": [item.to_dict() for item in self.code_blocks],
            "key_values": {
                key: [item.to_dict() for item in values]
                for key, values in self.key_values.items()
            },
            "sections": {
                key: [item.to_dict() for item in values]
                for key, values in self.sections.items()
            },
        }


KEY_VALUE_RE = re.compile(r"^\s*(?:[-*]\s*)?([A-Za-zÀ-ÿ0-9 _/-]{2,40})\s*[:=-]\s*(.+?)\s*$")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+)$")
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.+)$")
LINK_RE = re.compile(r"https?://[^\s)>\]]+|www\.[^\s)>\]]+", re.I)
TABLE_RE = re.compile(r"^\s*\|.+\|\s*$")


def parse_description(text: str | None, *, source: str = "trello.card.description") -> ParsedDescription:
    """Parse full Trello markdown description with line-level traceability."""
    raw = text or ""
    normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
    result = ParsedDescription(raw_text=raw, normalized_text=normalized)

    in_code = False
    current_section = "body"

    for index, line in enumerate(normalized.split("\n"), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        evidence = Evidence(source=source, line=index, evidence=stripped)
        result.lines.append(evidence)

        if stripped.startswith("```"):
            in_code = not in_code
            result.code_blocks.append(evidence)
            continue
        if in_code:
            result.code_blocks.append(evidence)
            continue

        heading = HEADING_RE.match(line)
        if heading:
            current_section = _normalize_key(heading.group(1))
            result.headings.append(evidence)
            result.sections.setdefault(current_section, []).append(evidence)
            continue

        if BULLET_RE.match(line):
            result.bullets.append(evidence)
        if TABLE_RE.match(line):
            result.tables.append(evidence)
        if LINK_RE.search(line):
            result.links.append(evidence)

        key_value = KEY_VALUE_RE.match(line)
        if key_value:
            key = _normalize_key(key_value.group(1))
            value = Evidence(source=source, line=index, evidence=key_value.group(2).strip())
            result.key_values.setdefault(key, []).append(value)

        result.sections.setdefault(current_section, []).append(evidence)

    return result


def _normalize_key(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-ZÀ-ÿ0-9]+", "_", value.strip().lower()).strip("_")
    return cleaned or "body"
