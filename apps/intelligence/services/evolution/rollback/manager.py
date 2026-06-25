from __future__ import annotations

import logging
from typing import Any

from apps.intelligence.services.evolution.storage import log_evolution_event
from apps.intelligence.services.evolution.versioning.core import SYSTEM_VERSION, version_snapshot

logger = logging.getLogger(__name__)

ROLLBACK_SNAPSHOTS: dict[str, dict[str, Any]] = {
    "1.0.0": {
        "system_version": "1.0.0",
        "eql_version": "1.0.0",
        "feature_flags": {
            "FEATURE_NEW_EQL_PARSER": False,
            "FEATURE_SEMANTIC_LAYER": False,
            "FEATURE_CMGL_ENFORCEMENT": False,
        },
    },
    "1.0.1": {
        "system_version": "1.0.1",
        "eql_version": "1.0.1",
        "feature_flags": {
            "FEATURE_SEMANTIC_LAYER": True,
            "FEATURE_CMGL_ENFORCEMENT": True,
        },
    },
}


def create_snapshot(label: str | None = None) -> dict[str, Any]:
    """Capture current system state for rollback."""
    snap = version_snapshot()
    snap["label"] = label or snap["system_version"]
    return snap


def rollback_to_version(target_version: str, *, initiated_by: str = "system") -> dict[str, Any]:
    """
    Rollback system to a previous version snapshot.
    Returns rollback manifest (does not mutate runtime env — records intent).
    """
    snapshot = ROLLBACK_SNAPSHOTS.get(target_version)
    if not snapshot:
        raise ValueError(f"No rollback snapshot for version {target_version}")

    manifest = {
        "status": "rolled_back",
        "from_version": version_snapshot()["system_version"],
        "to_version": target_version,
        "snapshot": snapshot,
        "restored_flags": snapshot.get("feature_flags", {}),
        "initiated_by": initiated_by,
    }

    log_evolution_event(
        version_from=manifest["from_version"],
        version_to=target_version,
        change_type="rollback",
        affected_layers=list(snapshot.keys()),
        risk_assessment={"risk_level": "LOW", "breaking_changes": []},
        status="completed",
        details=manifest,
    )
    logger.info("Rollback to %s initiated by %s", target_version, initiated_by)
    return manifest


def list_rollback_targets() -> list[str]:
    return sorted(ROLLBACK_SNAPSHOTS.keys())
