from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CURRENT_MODEL_VERSION = "1.1"

VERSION_HISTORY: dict[str, dict[str, Any]] = {
    "1.0": {
        "entity_types": ["INCIDENT", "DELIVERY", "PROJECT", "TASK"],
        "metrics": ["LEAD_TIME", "CYCLE_TIME", "RISK_SCORE", "SLA"],
        "breaking_changes": [],
    },
    "1.1": {
        "entity_types": [
            "INCIDENT", "DELIVERY", "PROJECT", "INITIATIVE", "TASK_GROUP",
            "RISK_EVENT", "BOTTLENECK", "SLA_CONTRACT", "WORKLOAD_UNIT", "TASK",
        ],
        "metrics": [
            "LEAD_TIME", "CYCLE_TIME", "RISK_SCORE", "SLA", "THROUGHPUT", "WIP",
            "INCIDENT_RATE", "DELIVERY_SUCCESS_RATE", "RISK_EXPOSURE_INDEX",
            "TEAM_LOAD_BALANCE", "OPERATIONAL_EFFICIENCY", "BOTTLENECK_DENSITY",
            "SLA_BREACH_PROBABILITY",
        ],
        "added": ["INCIDENT_RATE", "RISK_EXPOSURE_INDEX", "BOTTLENECK", "RISK_EVENT"],
        "breaking_changes": [],
    },
}


@dataclass
class VersionCompatibility:
    requested: str
    current: str
    compatible: bool
    missing_entities: list[str] = field(default_factory=list)
    missing_metrics: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def get_current_version() -> str:
    return CURRENT_MODEL_VERSION


def check_compatibility(requested_version: str, *, entity_types: list[str] | None = None, metrics: list[str] | None = None) -> VersionCompatibility:
    """Check if requested model version supports given entities/metrics."""
    result = VersionCompatibility(requested=requested_version, current=CURRENT_MODEL_VERSION, compatible=True)

    if requested_version not in VERSION_HISTORY:
        result.compatible = False
        result.warnings.append(f"Unknown model version: {requested_version}")
        return result

    spec = VERSION_HISTORY[requested_version]
    allowed_entities = set(spec.get("entity_types", []))
    allowed_metrics = set(spec.get("metrics", []))

    for et in entity_types or []:
        if et.upper() not in allowed_entities:
            result.missing_entities.append(et)
            result.compatible = False

    for m in metrics or []:
        if m.upper() not in allowed_metrics:
            result.missing_metrics.append(m)
            result.compatible = False

    if requested_version != CURRENT_MODEL_VERSION:
        result.warnings.append(f"Using version {requested_version}; current is {CURRENT_MODEL_VERSION}")

    return result


def migrate_metric_name(name: str, from_version: str = "1.0") -> str:
    """Map legacy metric names to current canonical names."""
    from apps.intelligence.services.core_model.registry import METRIC_ALIASES

    key = name.upper()
    if from_version == "1.0" and key in METRIC_ALIASES:
        return METRIC_ALIASES[key]
    return key
