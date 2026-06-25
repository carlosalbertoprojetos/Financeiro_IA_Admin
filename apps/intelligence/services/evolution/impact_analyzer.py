from __future__ import annotations

import re
from typing import Any

from apps.intelligence.services.evolution.compatibility.matrix import check_system_compatibility
from apps.intelligence.services.evolution.versioning.core import get_layer_versions


def analyze_change_impact(
    *,
    change_type: str,
    from_version: str,
    to_version: str | None = None,
    sample_queries: list[str] | None = None,
    affected_metrics: list[str] | None = None,
) -> dict[str, Any]:
    """
    Simulate impact of a version change before deployment.
    """
    lv = get_layer_versions()
    to_version = to_version or lv.system
    compat = check_system_compatibility(from_version, to_version)

    affected_queries: list[dict[str, Any]] = []
    for q in sample_queries or []:
        issues = _analyze_query_impact(q, from_version, to_version)
        if issues:
            affected_queries.append({"query_preview": q[:200], "issues": issues})

    breaking: list[str] = []
    warnings: list[str] = []
    if compat["overall"] == "BREAK":
        breaking.append(f"System upgrade {from_version} -> {to_version} has BREAK compatibility")
    for layer, level in compat["layers"].items():
        if level == "BREAK":
            breaking.append(f"Layer {layer} incompatible")
        elif level == "WARN":
            warnings.append(f"Layer {layer} requires migration (WARN)")

    metrics_affected = list(affected_metrics or [])
    if change_type == "metrics":
        metrics_affected.extend(["RISK_SCORE", "INCIDENT_RATE"])

    risk = _assess_risk(compat["overall"], len(affected_queries), len(breaking))

    return {
        "change_type": change_type,
        "from_version": from_version,
        "to_version": to_version,
        "affected_queries": affected_queries,
        "affected_metrics": metrics_affected,
        "risk_level": risk,
        "breaking_changes": breaking,
        "warnings": warnings,
        "compatibility": compat,
        "requires_migration": compat["overall"] in ("WARN", "BREAK"),
    }


def _analyze_query_impact(query: str, from_v: str, to_v: str) -> list[str]:
    issues: list[str] = []
    if re.search(r"\bRISK\s*=", query, re.I):
        issues.append("Legacy RISK= syntax requires adapter")
    if "ENTITY_TYPE" in query and from_v < "1.0.0":
        issues.append("Semantic filters require semantic_layer >= 1.0.0")
    if from_v != to_v and from_v.split(".")[0] != to_v.split(".")[0]:
        issues.append("Major version change may break query")
    return issues


def _assess_risk(overall: str, query_count: int, break_count: int) -> str:
    if overall == "BREAK" or break_count > 0:
        return "HIGH"
    if overall == "WARN" or query_count > 0:
        return "MEDIUM"
    return "LOW"
