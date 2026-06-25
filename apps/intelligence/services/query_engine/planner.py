"""Legacy planner — delegates to QCL compiler."""

from __future__ import annotations

from dataclasses import dataclass

from apps.intelligence.services.eql.ast import EQLQuery
from apps.intelligence.services.query_engine.compiler.compiler import compile_ast


@dataclass
class QueryPlan:
    """Deprecated: use query_engine.compiler.QueryPlan instead."""

    board_id: str
    use_timeline: bool
    use_cards: bool
    use_enrichment: bool
    use_precomputed_scores: bool
    filter_pushdown: list[str]
    metrics: list[str]
    group_by: list[str]
    sort: list[dict[str, str]]
    limit: int
    max_scan_cards: int = 5000

    @classmethod
    def from_ast(cls, query: EQLQuery) -> QueryPlan:
        compiled = compile_ast(query)
        pushdown = [f.field for f in compiled.filters if f.pushdown]
        return cls(
            board_id=compiled.board_id,
            use_timeline=compiled.scan.source == "timeline_events",
            use_cards=True,
            use_enrichment=compiled.scan.source == "enriched_context",
            use_precomputed_scores=False,
            filter_pushdown=pushdown,
            metrics=compiled.metrics,
            group_by=compiled.grouping,
            sort=compiled.sorting,
            limit=compiled.limit,
            max_scan_cards=compiled.max_scan_rows,
        )
