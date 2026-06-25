from __future__ import annotations

from typing import Any

from apps.intelligence.services.core_model.versioning import get_current_version

METRIC_FORMULAS: dict[str, dict[str, Any]] = {
    "LEAD_TIME": {
        "formula": "completed_at - created_at (hours)",
        "layer": "query_engine",
        "events": ["CARD_CREATED", "CARD_COMPLETED"],
    },
    "CYCLE_TIME": {
        "formula": "last_move - first_move (hours)",
        "layer": "query_engine",
        "events": ["CARD_MOVED"],
    },
    "RISK_SCORE": {
        "formula": "weighted_sum_v1.2(overdue, movements, assignee_churn, reopened, comm, checklist, stagnant)",
        "layer": "risk_engine",
        "events": ["CARD_MOVED", "CARD_ASSIGNED", "CARD_REOPENED", "COMMENT_ADDED"],
    },
    "SLA": {
        "formula": "due_at vs completed_at compliance",
        "layer": "query_engine",
        "events": ["DUE_DATE_CHANGED", "CARD_COMPLETED"],
    },
    "INCIDENT_RATE": {
        "formula": "incidents / total_entities * 100",
        "layer": "semantic_metrics_engine",
        "events": ["CARD_DELAYED", "BLOCKER_REGISTERED"],
    },
    "DELIVERY_SUCCESS_RATE": {
        "formula": "completed_deliveries / total_deliveries * 100",
        "layer": "semantic_metrics_engine",
        "events": ["CARD_COMPLETED"],
    },
    "RISK_EXPOSURE_INDEX": {
        "formula": "avg_risk_score + risk_entity_ratio * 20",
        "layer": "semantic_metrics_engine",
        "events": ["CARD_MOVED", "CARD_DELAYED"],
    },
    "BOTTLENECK_DENSITY": {
        "formula": "bottleneck_entities / total * 100",
        "layer": "semantic_metrics_engine",
        "events": ["CARD_MOVED"],
    },
}


def build_metrics_lineage(
    output: dict[str, Any],
    *,
    card_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Build lineage for each calculated metric."""
    model_version = get_current_version()
    lineage: list[dict[str, Any]] = []
    card_rows = card_rows or output.get("cards", [])

    technical = output.get("metrics", {})
    for key, spec in METRIC_FORMULAS.items():
        if key in technical or _snake(key) in technical:
            val = _extract_value(technical, key)
            lineage.append(_lineage_entry(key, val, spec, model_version, card_rows))

    for key, val in output.get("business_metrics", {}).items():
        canonical = key.upper()
        spec = METRIC_FORMULAS.get(canonical) or METRIC_FORMULAS.get(_screaming(key))
        if spec:
            lineage.append(_lineage_entry(_screaming(key), val.get("value") if isinstance(val, dict) else val, spec, model_version, card_rows))
        else:
            lineage.append({
                "metric": _screaming(key),
                "value": val.get("value") if isinstance(val, dict) else val,
                "layer": "semantic_metrics_engine",
                "formula": "derived",
                "event_sources": [],
                "model_version": model_version,
                "card_count": len(card_rows),
            })

    for row in card_rows:
        if row.get("risk_score") is not None:
            lineage.append({
                "metric": "RISK_SCORE",
                "value": row["risk_score"],
                "layer": "risk_engine",
                "formula": METRIC_FORMULAS["RISK_SCORE"]["formula"],
                "event_sources": METRIC_FORMULAS["RISK_SCORE"]["events"],
                "model_version": model_version,
                "card_id": row.get("card_id", row.get("trello_id")),
            })

    return _dedupe_lineage(lineage)


def _lineage_entry(name: str, value: Any, spec: dict[str, Any], model_version: str, card_rows: list) -> dict[str, Any]:
    return {
        "metric": name,
        "value": value,
        "layer": spec["layer"],
        "formula": spec["formula"],
        "event_sources": spec["events"],
        "model_version": model_version,
        "card_count": len(card_rows),
    }


def _extract_value(metrics: dict, key: str) -> Any:
    val = metrics.get(key) or metrics.get(_snake(key))
    if isinstance(val, dict):
        return val.get("avg") or val.get("value") or val.get("compliance_pct")
    return val


def _snake(key: str) -> str:
    return key.lower()


def _screaming(key: str) -> str:
    return key.upper().replace(" ", "_")


def _dedupe_lineage(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        key = f"{item['metric']}:{item.get('card_id', 'aggregate')}"
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result
