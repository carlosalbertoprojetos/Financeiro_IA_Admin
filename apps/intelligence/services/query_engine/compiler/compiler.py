from __future__ import annotations

from typing import Any

from apps.intelligence.services.eql.ast import EQLQuery
from apps.intelligence.services.query_engine.compiler.plan import (
    FilterStep,
    PreAggregation,
    QueryPlan,
    ScanSpec,
)

FILTER_STAGE_MAP = {
    "period": "scan",
    "title_prefix": "scan",
    "labels": "post_scan",
    "members": "post_scan",
    "status": "post_scan",
    "risk_score": "post_join",
    "lead_time": "post_join",
    "cycle_time": "post_join",
}


def compile_ast(query: EQLQuery | dict[str, Any]) -> QueryPlan:
    """Convert validated EQL AST into a structured Query Plan. Does not execute data."""
    if isinstance(query, EQLQuery):
        ast = query.to_dict()
    else:
        ast = query

    filters_raw = ast.get("filters", {})
    filter_steps = _build_filter_steps(filters_raw)
    scan = _select_initial_scan(filters_raw, ast.get("metrics", []))
    grouping = [g.upper() for g in ast.get("group_by", [])]
    sorting = list(ast.get("sort", [{"field": "RISK_SCORE", "order": "DESC"}]))
    metrics = [m.upper() for m in ast.get("metrics", [])]
    limit = int(ast.get("limit", 100))

    pre_agg = [PreAggregation(dimension=g) for g in grouping]

    strategy: str = "SEQUENTIAL"
    independent = _independent_filter_dimensions(filters_raw)
    if len(independent) >= 2:
        strategy = "PARALLEL"

    return QueryPlan(
        report_type=ast.get("type", "EXECUTIVE"),
        board_id=ast.get("board_id", ""),
        scan=scan,
        filters=filter_steps,
        pre_aggregations=pre_agg,
        grouping=grouping,
        sorting=sorting,
        limit=min(limit, 1000),
        metrics=metrics,
        execution_strategy=strategy,  # type: ignore[arg-type]
        max_scan_rows=min(max(limit * 50, 500), 5000),
    )


def _build_filter_steps(filters: dict[str, Any]) -> list[FilterStep]:
    steps: list[FilterStep] = []
    for field, spec in filters.items():
        stage = FILTER_STAGE_MAP.get(field, "post_scan")
        steps.append(
            FilterStep(
                field=field,
                stage=stage,  # type: ignore[arg-type]
                spec=spec if isinstance(spec, dict) else {"value": spec},
                pushdown=stage == "scan",
            )
        )
    return steps


def _select_initial_scan(filters: dict[str, Any], metrics: list[str]) -> ScanSpec:
    if "period" in filters:
        secondary: list[str] = ["cards"]
        if any(k in filters for k in ("labels", "title_prefix")):
            secondary.append("enriched_context")
        return ScanSpec(source="timeline_events", secondary_sources=secondary)  # type: ignore[arg-type]

    if any(k in filters for k in ("labels", "title_prefix")):
        return ScanSpec(source="enriched_context", secondary_sources=["cards"])

    if "RISK_SCORE" in [m.upper() for m in metrics]:
        return ScanSpec(source="cards", secondary_sources=["enriched_context"])

    return ScanSpec(source="cards")


def _independent_filter_dimensions(filters: dict[str, Any]) -> list[str]:
    """Dimensions that can be evaluated independently (labels vs members vs status)."""
    independent = []
    for key in ("labels", "members", "status"):
        if key in filters:
            independent.append(key)
    return independent
