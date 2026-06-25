from __future__ import annotations

import re
from typing import Any

# Legacy EQL field → modern EQL
FIELD_MIGRATIONS: list[tuple[str, str]] = [
    (r"\bRISK\s*=\s*HIGH\b", "RISK_LEVEL >= HIGH"),
    (r"\bRISK\s*=\s*CRITICAL\b", "RISK_LEVEL >= CRITICAL"),
    (r"\bRISK\s*=\s*MEDIUM\b", "RISK_LEVEL >= MEDIUM"),
    (r"\bRISK\s*=\s*LOW\b", "RISK_LEVEL >= LOW"),
    (r"\bFAILURE_RATE\b", "INCIDENT_RATE"),
    (r"\bTASK_COMPLETION\b", "DELIVERY"),
    (r"\bTYPE\s*=\s*EXECUTIVO\b", "TYPE = EXECUTIVE"),
    (r"\bTYPE\s*=\s*OPERACIONAL\b", "TYPE = OPERATIONAL"),
]

RISK_SCORE_THRESHOLDS = {
    "HIGH": 50,
    "CRITICAL": 75,
    "MEDIUM": 25,
    "LOW": 0,
}


def adapt_legacy_query(query_text: str, *, source_version: str = "1.0.0") -> tuple[str, list[dict[str, Any]]]:
    """
    Translate legacy EQL to current format.
    Returns adapted query and list of adaptations applied.
    """
    if source_version >= "1.1.0":
        return query_text, []

    adapted = query_text
    changes: list[dict[str, Any]] = []

    for pattern, replacement in FIELD_MIGRATIONS:
        if re.search(pattern, adapted, re.I):
            before = adapted
            adapted = re.sub(pattern, replacement, adapted, flags=re.I)
            changes.append({"type": "field_migration", "from": pattern, "to": replacement, "layer": "eql"})

    adapted, risk_changes = _adapt_risk_level_syntax(adapted)
    changes.extend(risk_changes)

    if "LIMIT" not in adapted.upper() and "limit:" not in adapted.lower():
        adapted = adapted.rstrip() + "\n\nLIMIT:\n100"
        changes.append({"type": "default_injection", "field": "LIMIT", "value": 100})

    return adapted, changes


def _adapt_risk_level_syntax(text: str) -> tuple[str, list[dict[str, Any]]]:
    changes: list[dict[str, Any]] = []
    match = re.search(r"RISK_LEVEL\s*>=\s*(HIGH|CRITICAL|MEDIUM|LOW)", text, re.I)
    if match:
        level = match.group(1).upper()
        threshold = RISK_SCORE_THRESHOLDS.get(level, 50)
        replacement = f"RISK_SCORE >= {threshold}"
        text = re.sub(r"RISK_LEVEL\s*>=\s*(HIGH|CRITICAL|MEDIUM|LOW)", replacement, text, flags=re.I)
        changes.append({"type": "risk_level_to_score", "level": level, "threshold": threshold})
    return text, changes


def detect_query_version(query_text: str) -> str:
    """Heuristic detection of query EQL version."""
    if re.search(r"\bRISK\s*=", query_text, re.I) and not re.search(r"RISK_SCORE|RISK_LEVEL", query_text, re.I):
        return "1.0.0"
    if re.search(r"\bENTITY_TYPE\b", query_text, re.I):
        return "1.1.0"
    return "1.0.1"
