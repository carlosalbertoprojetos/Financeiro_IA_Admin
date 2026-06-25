from __future__ import annotations

from typing import Any

from apps.intelligence.services.observability.context import get_collector


def record_error_trace(
    *,
    code: str,
    message: str,
    layer: str,
    query_id: str = "",
    details: dict[str, Any] | None = None,
) -> None:
    collector = get_collector()
    if collector:
        collector.record_error(code, message, layer, **(details or {}))
    return None


def record_governance_block(message: str, code: str = "GOVERNANCE_REJECTED") -> None:
    record_error_trace(code=code, message=message, layer="core_model")


def record_semantic_inconsistency(conflicts: list[dict[str, Any]]) -> None:
    record_error_trace(
        code="SEMANTIC_INCONSISTENCY",
        message=f"{len(conflicts)} semantic conflicts detected",
        layer="core_model",
        details={"conflicts": conflicts[:10]},
    )


def record_guard_rejection(message: str, code: str = "QUERY_GUARD_REJECTED") -> None:
    record_error_trace(code=code, message=message, layer="query_guard")
