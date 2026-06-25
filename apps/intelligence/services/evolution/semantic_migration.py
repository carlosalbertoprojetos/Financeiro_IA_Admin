from __future__ import annotations

from typing import Any

ENTITY_MIGRATIONS: dict[str, str] = {
    "FAILURE": "INCIDENT",
    "TASK_COMPLETION": "DELIVERY",
    "BLOCKER": "BOTTLENECK",
    "WORK_ITEM": "TASK",
}

ENTITY_RECLASSIFICATION: dict[str, dict[str, Any]] = {
    "INCIDENT": {
        "to": "RISK_EVENT",
        "condition": lambda e: e.get("risk_score", 0) >= 75 and "external_dependency" in e.get("risk_flags", []),
    },
}


def migrate_entity(entity: dict[str, Any], *, from_version: str = "1.0.0") -> tuple[dict[str, Any], list[str]]:
    """Migrate a business entity dict to current taxonomy."""
    changes: list[str] = []
    migrated = dict(entity)
    et = migrated.get("entity_type", "")

    if et in ENTITY_MIGRATIONS:
        new_type = ENTITY_MIGRATIONS[et]
        changes.append(f"entity_type:{et}->{new_type}")
        migrated["entity_type"] = new_type
        et = new_type

    reclass = ENTITY_RECLASSIFICATION.get(et)
    if reclass and reclass["condition"](migrated):
        new_type = reclass["to"]
        changes.append(f"reclassify:{et}->{new_type}")
        migrated["entity_type"] = new_type

    if from_version < "1.1.0" and migrated.get("category") == "FINANCEIRO":
        migrated.setdefault("metadata", {})["legacy_category"] = True
        changes.append("category:marked_legacy")

    return migrated, changes


def migrate_entities(entities: list[dict[str, Any]], *, from_version: str = "1.0.0") -> tuple[list[dict[str, Any]], list[str]]:
    all_changes: list[str] = []
    result: list[dict[str, Any]] = []
    for entity in entities:
        migrated, changes = migrate_entity(entity, from_version=from_version)
        result.append(migrated)
        all_changes.extend(changes)
    return result, all_changes


def migrate_metric_keys(metrics: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Migrate legacy metric keys in output."""
    from apps.intelligence.services.core_model.registry import METRIC_ALIASES

    changes: list[str] = []
    migrated: dict[str, Any] = {}
    for key, val in metrics.items():
        upper = key.upper().replace(" ", "_")
        if upper in METRIC_ALIASES:
            new_key = METRIC_ALIASES[upper].lower()
            changes.append(f"metric:{key}->{new_key}")
            migrated[new_key] = val
        else:
            migrated[key] = val
    return migrated, changes
