from __future__ import annotations

from typing import Any

from apps.intelligence.services.observability.ai_trace import trace_recommendations
from apps.intelligence.services.observability.config import is_debug_mode
from apps.intelligence.services.observability.context import set_collector
from apps.intelligence.services.observability.execution_trace import (
    record_cache_event,
    record_governance,
    record_optimization,
)
from apps.intelligence.services.observability.lineage.metrics_lineage import build_metrics_lineage
from apps.intelligence.services.observability.lineage.query_lineage import build_query_lineage
from apps.intelligence.services.observability.storage import persist_trace
from apps.intelligence.services.observability.trace.collector import TraceCollector


def finalize_pipeline_trace(
    collector: TraceCollector,
    output: dict[str, Any],
    *,
    query_raw: str,
    execution_ms: int,
    status: str = "success",
) -> dict[str, Any]:
    """Build lineage, metrics trace, persist and attach to output."""
    lineage = build_query_lineage(
        query_raw=query_raw,
        ast=output.get("query_ast", {}),
        query_plan=output.get("query_plan"),
        optimized_plan=output.get("optimized_plan"),
        cost_estimate=output.get("cost_estimate"),
        governance=output.get("governance"),
    )
    collector.set_query_lineage(lineage)

    metrics_lineage = build_metrics_lineage(output)
    for ml in metrics_lineage:
        if ml.get("card_id"):
            continue
        collector.record_metric(
            ml["metric"],
            ml.get("value"),
            layer=ml["layer"],
            formula=ml["formula"],
            sources=ml.get("event_sources", []),
            model_version=ml.get("model_version", "1.1"),
        )

    if output.get("domain_insights"):
        trace_recommendations(output["domain_insights"])

    opt_notes = output.get("optimized_plan", {}).get("optimization_notes", [])
    if opt_notes:
        record_optimization(opt_notes)

    if output.get("governance"):
        record_governance(output["governance"])

    trace = collector.finalize(output, execution_ms=execution_ms, status=status)
    persist_trace(trace, query_raw=query_raw, board_id=output.get("summary", {}).get("board_id", ""))

    output["trace_id"] = trace.trace_id
    output["query_id"] = trace.query_id

    if is_debug_mode():
        output["decision_trace"] = trace.to_dict()
        output["metrics_lineage"] = metrics_lineage

    set_collector(None)
    return output
