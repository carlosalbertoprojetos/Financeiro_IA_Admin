from __future__ import annotations

from apps.intelligence.services.query_engine.compiler.plan import (
    FilterStep,
    OptimizedQueryPlan,
    QueryPlan,
)

STAGE_PRIORITY = {"scan": 0, "post_scan": 1, "post_join": 2}


def optimize_plan(plan: QueryPlan) -> OptimizedQueryPlan:
    """
    Rewrite Query Plan for maximum efficiency.
    Does not execute data — only transforms the plan.
    """
    notes: list[str] = []
    filters = _pushdown_filters(plan.filters, notes)
    scan = _optimize_scan_source(plan, filters, notes)
    early_limit = _apply_early_limit(plan, notes)
    pre_agg = list(plan.pre_aggregations)
    if plan.grouping:
        notes.append("pre_aggregate_before_metrics")
    parallel_dims = _detect_parallel_dimensions(filters, plan.execution_strategy, notes)

    pushdown_order = [f.field for f in filters if f.pushdown]
    pushdown_order.extend(f.field for f in filters if not f.pushdown)

    return OptimizedQueryPlan(
        report_type=plan.report_type,
        board_id=plan.board_id,
        scan=scan,
        filters=filters,
        pre_aggregations=pre_agg,
        grouping=list(plan.grouping),
        sorting=list(plan.sorting),
        limit=plan.limit,
        metrics=list(plan.metrics),
        execution_strategy="PARALLEL" if parallel_dims else plan.execution_strategy,
        max_scan_rows=_tighten_scan_limit(plan, early_limit),
        early_limit=early_limit,
        filter_pushdown_order=pushdown_order,
        parallel_dimensions=parallel_dims,
        optimization_notes=notes,
    )


def _pushdown_filters(filters: list[FilterStep], notes: list[str]) -> list[FilterStep]:
    """Move filters to earliest possible stage."""
    optimized: list[FilterStep] = []
    for f in filters:
        step = FilterStep(
            field=f.field,
            stage=f.stage,
            spec=f.spec,
            pushdown=f.stage == "scan" or f.field in ("title_prefix", "labels", "members", "status"),
        )
        if step.pushdown and f.stage != "scan":
            step = FilterStep(field=f.field, stage="post_scan", spec=f.spec, pushdown=True)
            notes.append(f"filter_pushdown:{f.field}")
        optimized.append(step)

    optimized.sort(key=lambda x: (STAGE_PRIORITY.get(x.stage, 99), x.field))
    return optimized


def _optimize_scan_source(plan: QueryPlan, filters: list[FilterStep], notes: list[str]):
    scan = plan.scan
    has_period = any(f.field == "period" for f in filters)
    has_enrichment = any(f.field in ("labels", "title_prefix") for f in filters)

    if has_period and scan.source != "timeline_events":
        notes.append("source_selection:timeline_events")
        from apps.intelligence.services.query_engine.compiler.plan import ScanSpec

        secondary = ["cards"]
        if has_enrichment:
            secondary.append("enriched_context")
        return ScanSpec(source="timeline_events", secondary_sources=secondary)  # type: ignore[arg-type]

    if has_enrichment and scan.source == "cards":
        notes.append("source_selection:enriched_context")
        from apps.intelligence.services.query_engine.compiler.plan import ScanSpec

        return ScanSpec(source="enriched_context", secondary_sources=["cards"])

    return scan


def _apply_early_limit(plan: QueryPlan, notes: list[str]) -> bool:
    if plan.limit and plan.limit <= 500:
        notes.append("early_limit_applied")
        return True
    return False


def _detect_parallel_dimensions(
    filters: list[FilterStep],
    strategy: str,
    notes: list[str],
) -> list[str]:
    independent = [f.field for f in filters if f.field in ("labels", "members", "status")]
    if len(independent) >= 2:
        notes.append("parallel_execution_enabled")
        return independent
    return []


def _tighten_scan_limit(plan: QueryPlan, early_limit: bool) -> int:
    if early_limit:
        return min(plan.max_scan_rows, max(plan.limit * 20, 200))
    return plan.max_scan_rows
