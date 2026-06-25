from __future__ import annotations

from typing import Any

from apps.intelligence.services.core_model.errors import (
    GovernanceError,
    SemanticInconsistencyError,
    UnregisteredEntityError,
    UnregisteredEventError,
    UnregisteredMetricError,
)
from apps.intelligence.services.core_model.registry import REGISTRY
from apps.intelligence.services.core_model.semantic_consistency import analyze_consistency
from apps.intelligence.services.core_model.validator import (
    validate_cross_layer,
    validate_eql_ast,
    validate_query_plan,
    validate_semantic_output,
)
from apps.intelligence.services.core_model.versioning import check_compatibility, get_current_version


def enforce_eql_ast(ast: dict[str, Any], *, model_version: str | None = None) -> None:
    """Block execution if EQL AST violates governance rules."""
    version = model_version or get_current_version()
    entity_types = [
        v for v in ast.get("semantic_filters", {}).get("entity_type", {}).get("values", [])
    ]
    compat = check_compatibility(version, entity_types=entity_types, metrics=ast.get("metrics"))
    if not compat.compatible:
        raise GovernanceError(
            f"Model version {version} incompatible with query",
            code="MODEL_VERSION_ERROR",
            details=compat.__dict__,
        )
    validate_eql_ast(ast)


def enforce_query_plan(plan: dict[str, Any]) -> None:
    """Block if query plan contains non-canonical constructs."""
    validate_query_plan(plan)


def enforce_semantic_output(output: dict[str, Any], *, strict: bool = True) -> dict[str, Any]:
    """Validate and enforce governance on semantic layer output."""
    validate_semantic_output(output)
    consistency = analyze_consistency(output)
    if strict and not consistency["consistent"]:
        raise SemanticInconsistencyError(
            "Semantic inconsistencies detected in output",
            details=consistency,
        )
    return consistency


def enforce_entity_type(entity_type: str) -> str:
    """Resolve and enforce canonical entity type."""
    resolved = REGISTRY.resolve_entity_type(entity_type)
    if not resolved:
        raise UnregisteredEntityError(
            f"Entity type not registered: {entity_type}",
            details={"entity_type": entity_type, "registered": sorted(REGISTRY.entity_types)},
        )
    return resolved


def enforce_metric(metric: str) -> str:
    """Resolve and enforce canonical metric name."""
    resolved = REGISTRY.resolve_metric(metric)
    if not resolved:
        raise UnregisteredMetricError(
            f"Metric not registered: {metric}",
            details={"metric": metric, "registered": sorted(REGISTRY.metrics)},
        )
    return resolved


def enforce_event(event_type: str) -> None:
    """Block unknown event types."""
    if not REGISTRY.is_event_registered(event_type):
        raise UnregisteredEventError(
            f"Event type not registered: {event_type}",
            details={"event_type": event_type},
        )


def govern_pipeline(
    *,
    ast: dict[str, Any] | None = None,
    query_plan: dict[str, Any] | None = None,
    output: dict[str, Any] | None = None,
    strict: bool = True,
) -> dict[str, Any]:
    """
    Full CMGL governance pass across pipeline stages.
    Returns governance metadata attached to output.
    """
    if ast is not None:
        enforce_eql_ast(ast)

    if query_plan is not None:
        enforce_query_plan(query_plan)

    consistency: dict[str, Any] = {"consistent": True, "conflicts": []}
    if output is not None:
        consistency = enforce_semantic_output(output, strict=strict)

    cross = validate_cross_layer(ast=ast, query_plan=query_plan, semantic_output=output)

    return {
        "model_version": get_current_version(),
        "registry_snapshot": REGISTRY.to_dict(),
        "cross_layer_validation": cross,
        "semantic_consistency": consistency,
        "governed": cross.get("valid", True) and consistency.get("consistent", True),
    }
