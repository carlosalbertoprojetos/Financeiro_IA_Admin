from __future__ import annotations

import logging
from typing import Any

from apps.intelligence.services.query_engine.aggregation import (
    apply_risk_score_filter,
    ast_to_payload,
    build_standard_output,
)
from apps.intelligence.services.query_engine.compiler.plan import OptimizedQueryPlan
from apps.intelligence.services.report_query.engine.post_processor import (
    build_card_rows,
    build_grouped_summary,
    build_metrics_summary,
)
from apps.intelligence.services.report_query.engine.queryset_builder import build_filtered_cards
from apps.intelligence.services.report_query.templates.registry import generate_report

logger = logging.getLogger(__name__)


def execute_optimized_plan(
    plan: OptimizedQueryPlan,
    *,
    ast_dict: dict[str, Any],
    processing_start_ms: float | None = None,
) -> dict[str, Any]:
    """
    Execute an optimized query plan against data sources.
    Does NOT optimize or interpret EQL — only executes the plan as given.
    """
    import time

    start = processing_start_ms if processing_start_ms is not None else time.perf_counter()

    payload = ast_to_payload(ast_dict)
    if plan.early_limit:
        payload.limit = min(payload.limit, plan.limit)

    cards, filters_meta = build_filtered_cards(payload)
    cards = _apply_post_join_filters(cards, plan)

    if plan.early_limit and len(cards) > plan.max_scan_rows:
        cards = cards[: plan.max_scan_rows]

    card_rows = build_card_rows(cards, payload)
    metrics_summary = build_metrics_summary(card_rows, payload.metrics)
    grouped = build_grouped_summary(card_rows, payload.group_by) if plan.grouping else {}

    processing_ms = int((time.perf_counter() - start) * 1000)

    output = build_standard_output(
        query_ast=ast_dict,
        cards=cards,
        card_rows=card_rows,
        metrics_summary=metrics_summary,
        grouped=grouped,
        processing_ms=processing_ms,
    )
    output["report"] = generate_report(
        payload.report_type,
        cards,
        board_id=payload.board_id,
        filters_meta=filters_meta,
    )
    output["execution_plan"] = {
        "scan": plan.scan.to_dict(),
        "execution_strategy": plan.execution_strategy,
        "early_limit": plan.early_limit,
        "filter_pushdown_order": plan.filter_pushdown_order,
        "parallel_dimensions": plan.parallel_dimensions,
        "optimization_notes": plan.optimization_notes,
    }
    return output


def _apply_post_join_filters(cards: list, plan: OptimizedQueryPlan) -> list:
    for step in plan.filters:
        if step.field == "risk_score":
            cards = apply_risk_score_filter(cards, step.spec)
    return cards


def compute_actual_cost(matched_cards: int, processing_ms: int, plan: OptimizedQueryPlan) -> int:
    """Compute actual execution cost score (0-100) after execution."""
    cost = min(50, matched_cards // 20)
    cost += min(30, processing_ms // 1000)
    if plan.grouping:
        cost += 10
    return min(100, cost)
