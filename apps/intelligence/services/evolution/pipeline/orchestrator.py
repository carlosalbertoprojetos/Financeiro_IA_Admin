from __future__ import annotations

from typing import Any

from apps.intelligence.services.evolution.compatibility.query_adapter import adapt_legacy_query, detect_query_version
from apps.intelligence.services.evolution.config import is_safe_mode
from apps.intelligence.services.evolution.impact_analyzer import analyze_change_impact
from apps.intelligence.services.evolution.storage import log_evolution_event
from apps.intelligence.services.evolution.versioning.core import get_system_version, version_snapshot


def prepare_query_for_execution(query_text: str) -> tuple[str, dict[str, Any]]:
    """
    ECP pre-execution hook: adapt legacy queries, record evolution metadata.
    """
    detected = detect_query_version(query_text)
    adapted, changes = adapt_legacy_query(query_text, source_version=detected)
    meta = {
        "detected_version": detected,
        "adaptations": changes,
        "adapted": len(changes) > 0,
        "system_version": get_system_version(),
        "layers": version_snapshot()["layers"],
    }
    return adapted, meta


def validate_deployment(change: dict[str, Any]) -> dict[str, Any]:
    """
    Safe deployment pipeline step: validate compatibility and simulate impact.
    """
    from_v = change.get("from_version", "1.0.0")
    to_v = change.get("to_version", get_system_version())
    impact = analyze_change_impact(
        change_type=change.get("change_type", "upgrade"),
        from_version=from_v,
        to_version=to_v,
        sample_queries=change.get("sample_queries", []),
        affected_metrics=change.get("affected_metrics", []),
    )

    if is_safe_mode() and impact["risk_level"] == "HIGH":
        log_evolution_event(
            version_from=from_v,
            version_to=to_v,
            change_type=change.get("change_type", "upgrade"),
            affected_layers=list(impact["compatibility"]["layers"].keys()),
            risk_assessment=impact,
            status="rejected",
        )
        impact["approved"] = False
        impact["reason"] = "SAFE_MODE blocked HIGH risk change"
        return impact

    log_evolution_event(
        version_from=from_v,
        version_to=to_v,
        change_type=change.get("change_type", "upgrade"),
        affected_layers=list(impact["compatibility"]["layers"].keys()),
        risk_assessment=impact,
        status="approved" if impact["risk_level"] != "HIGH" else "pending_review",
    )
    impact["approved"] = impact["risk_level"] != "HIGH" or not is_safe_mode()
    return impact


def run_evolution_pipeline(change: dict[str, Any]) -> dict[str, Any]:
    """
    Full ECP pipeline:
    1. Detect change
    2. Validate compatibility
    3. Simulate impact
    4. Approve/reject (safe mode)
    5. Log audit
    """
    validation = validate_deployment(change)
    return {
        "pipeline": "ecp",
        "steps_completed": ["detect", "validate", "impact_simulation", "audit_log"],
        "validation": validation,
        "safe_mode": is_safe_mode(),
    }
