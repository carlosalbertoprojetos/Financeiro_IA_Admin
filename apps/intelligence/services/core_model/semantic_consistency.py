from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apps.intelligence.services.core_model.registry import METRIC_ALIASES, ENTITY_ALIASES, REGISTRY


@dataclass
class SemanticConflict:
    conflict_type: str
    term_a: str
    term_b: str
    message: str
    severity: str = "warning"

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflict_type": self.conflict_type,
            "term_a": self.term_a,
            "term_b": self.term_b,
            "message": self.message,
            "severity": self.severity,
        }


KNOWN_DUPLICATE_PAIRS = [
    ("INCIDENT_RATE", "FAILURE_RATE", "Same concept: operational failure frequency"),
    ("DELIVERY_SUCCESS_RATE", "TASK_COMPLETION_RATE", "Same concept: successful completion rate"),
    ("RISK_SCORE", "RISK_EXPOSURE_INDEX", "Related but distinct: score vs aggregate index"),
    ("DELIVERY", "TASK_COMPLETION", "Same entity concept with different names"),
    ("BOTTLENECK", "BLOCKER", "Same entity concept with different names"),
]


def detect_metric_conflicts(metrics: list[str]) -> list[SemanticConflict]:
    """Detect semantically duplicate or conflicting metrics in a query/report."""
    conflicts: list[SemanticConflict] = []
    normalized = {m.upper(): m for m in metrics}
    resolved = {m: REGISTRY.resolve_metric(m) for m in normalized}

    for canonical_a, canonical_b, msg in [
        ("INCIDENT_RATE", "FAILURE_RATE", "Incident Rate vs Failure Rate"),
        ("DELIVERY_SUCCESS_RATE", "TASK_COMPLETION_RATE", "Delivery vs Task Completion"),
    ]:
        if canonical_a in normalized and canonical_b in normalized:
            conflicts.append(SemanticConflict("duplicate_metric", canonical_a, canonical_b, msg, "error"))

    seen_canonical: dict[str, str] = {}
    for raw, canonical in resolved.items():
        if not canonical:
            continue
        if canonical in seen_canonical and seen_canonical[canonical] != raw:
            conflicts.append(SemanticConflict(
                "alias_collision",
                seen_canonical[canonical],
                raw,
                f"Metrics {seen_canonical[canonical]} and {raw} resolve to same canonical {canonical}",
            ))
        seen_canonical[canonical] = raw

    if "RISK_SCORE" in normalized and "RISK_EXPOSURE_INDEX" in normalized:
        conflicts.append(SemanticConflict(
            "related_metrics",
            "RISK_SCORE",
            "RISK_EXPOSURE_INDEX",
            "Risk Score (card-level) and Risk Exposure Index (aggregate) — ensure distinct usage",
            "warning",
        ))

    return conflicts


def detect_entity_conflicts(entities: list[dict[str, Any]]) -> list[SemanticConflict]:
    """Detect overlapping or inconsistent entity classifications."""
    conflicts: list[SemanticConflict] = []
    by_card: dict[str, list[str]] = {}

    for entity in entities:
        card_id = entity.get("card_id", entity.get("entity_id", ""))
        et = entity.get("entity_type", "")
        by_card.setdefault(card_id, []).append(et)

    for card_id, types in by_card.items():
        unique = set(types)
        if len(unique) > 1 and "INCIDENT" in unique and "DELIVERY" in unique:
            conflicts.append(SemanticConflict(
                "overlapping_entity",
                "INCIDENT",
                "DELIVERY",
                f"Card {card_id} classified as both INCIDENT and DELIVERY",
                "error",
            ))

    return conflicts


def check_naming_consistency(output: dict[str, Any]) -> list[SemanticConflict]:
    """Check output for semantic naming inconsistencies across layers."""
    conflicts: list[SemanticConflict] = []

    ast_metrics = [m.upper() for m in output.get("query_ast", {}).get("metrics", [])]
    business_keys = list(output.get("business_metrics", {}).keys())

    for key in business_keys:
        normalized = key.upper().replace(" ", "_")
        if not REGISTRY.normalize_metric_key(key):
            conflicts.append(SemanticConflict(
                "unregistered_metric_output",
                key,
                "",
                f"Business metric '{key}' not in canonical registry",
                "error",
            ))

    conflicts.extend(detect_metric_conflicts(ast_metrics + [k.upper() for k in business_keys]))
    conflicts.extend(detect_entity_conflicts(output.get("entities", [])))

    for alias, canonical in ENTITY_ALIASES.items():
        if alias in ast_metrics and canonical in [e.get("entity_type") for e in output.get("entities", [])]:
            conflicts.append(SemanticConflict(
                "alias_entity_usage",
                alias,
                canonical,
                f"Alias {alias} used in query but output uses canonical {canonical}",
                "warning",
            ))

    return conflicts


def analyze_consistency(output: dict[str, Any]) -> dict[str, Any]:
    """Full semantic consistency analysis."""
    conflicts = check_naming_consistency(output)
    errors = [c for c in conflicts if c.severity == "error"]
    return {
        "consistent": len(errors) == 0,
        "conflict_count": len(conflicts),
        "errors": len(errors),
        "warnings": len(conflicts) - len(errors),
        "conflicts": [c.to_dict() for c in conflicts],
    }
