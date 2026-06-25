from __future__ import annotations

from typing import Any

from apps.intelligence.services.core_model.errors import CrossLayerValidationError
from apps.intelligence.services.core_model.registry import REGISTRY


def validate_eql_ast(ast: dict[str, Any]) -> list[str]:
    """Validate EQL AST against canonical registry."""
    issues: list[str] = []

    for metric in ast.get("metrics", []):
        if not REGISTRY.resolve_metric(str(metric)):
            issues.append(f"Unregistered metric in EQL: {metric}")

    semantic = ast.get("semantic_filters", {})
    entity_type = semantic.get("entity_type", {})
    for et in entity_type.get("values", []):
        if not REGISTRY.resolve_entity_type(str(et)):
            issues.append(f"Unregistered entity type in EQL: {et}")

    filters = ast.get("filters", {})
    for key in filters:
        if key.startswith("entity_") and key not in ("entity_type", "entity_status"):
            issues.append(f"Unknown semantic filter field: {key}")

    if issues:
        raise CrossLayerValidationError(
            "EQL AST failed governance validation",
            details={"layer": "eql", "issues": issues},
        )
    return issues


def validate_query_plan(plan: dict[str, Any]) -> list[str]:
    """Validate Query Engine plan against registry."""
    issues: list[str] = []

    for metric in plan.get("metrics", []):
        if not REGISTRY.resolve_metric(str(metric)):
            issues.append(f"Unregistered metric in query plan: {metric}")

    for f in plan.get("filters", []):
        field = f.get("field", "") if isinstance(f, dict) else str(f)
        if field.startswith("entity_") and field not in ("entity_type", "entity_status"):
            issues.append(f"Non-canonical filter in query plan: {field}")

    if issues:
        raise CrossLayerValidationError(
            "Query plan failed governance validation",
            details={"layer": "query_engine", "issues": issues},
        )
    return issues


def validate_semantic_output(output: dict[str, Any]) -> list[str]:
    """Validate Semantic Layer output against registry."""
    issues: list[str] = []

    for entity in output.get("entities", []):
        et = entity.get("entity_type", "")
        if not REGISTRY.resolve_entity_type(str(et)):
            issues.append(f"Unregistered entity type in semantic output: {et}")

    for metric_key in output.get("business_metrics", {}):
        canonical = REGISTRY.normalize_metric_key(metric_key)
        if not canonical:
            issues.append(f"Unregistered business metric: {metric_key}")

    for event in output.get("timeline", {}).get("events", []):
        et = event.get("event_type", "")
        if et and not REGISTRY.is_event_registered(et):
            issues.append(f"Unregistered event type: {et}")

    if issues:
        raise CrossLayerValidationError(
            "Semantic output failed governance validation",
            details={"layer": "semantic", "issues": issues},
        )
    return issues


def validate_cross_layer(
    *,
    ast: dict[str, Any] | None = None,
    query_plan: dict[str, Any] | None = None,
    semantic_output: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run full cross-layer validation pipeline."""
    results: dict[str, Any] = {"valid": True, "layers": {}}

    if ast is not None:
        try:
            validate_eql_ast(ast)
            results["layers"]["eql"] = "ok"
        except CrossLayerValidationError as exc:
            results["valid"] = False
            results["layers"]["eql"] = exc.details

    if query_plan is not None:
        try:
            validate_query_plan(query_plan)
            results["layers"]["query_engine"] = "ok"
        except CrossLayerValidationError as exc:
            results["valid"] = False
            results["layers"]["query_engine"] = exc.details

    if semantic_output is not None:
        try:
            validate_semantic_output(semantic_output)
            results["layers"]["semantic"] = "ok"
        except CrossLayerValidationError as exc:
            results["valid"] = False
            results["layers"]["semantic"] = exc.details

    return results
