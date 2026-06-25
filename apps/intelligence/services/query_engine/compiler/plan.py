from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ScanSource = Literal["timeline_events", "cards", "enriched_context"]
ExecutionStrategy = Literal["SEQUENTIAL", "PARALLEL"]


@dataclass
class ScanSpec:
    source: ScanSource = "cards"
    secondary_sources: list[ScanSource] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"source": self.source, "secondary_sources": list(self.secondary_sources)}


@dataclass
class FilterStep:
    field: str
    stage: Literal["scan", "post_scan", "post_join"] = "scan"
    spec: dict[str, Any] = field(default_factory=dict)
    pushdown: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "stage": self.stage,
            "spec": self.spec,
            "pushdown": self.pushdown,
        }


@dataclass
class PreAggregation:
    dimension: str
    strategy: Literal["hash", "sort"] = "hash"

    def to_dict(self) -> dict[str, Any]:
        return {"dimension": self.dimension, "strategy": self.strategy}


@dataclass
class QueryPlan:
    report_type: str
    board_id: str
    scan: ScanSpec
    filters: list[FilterStep] = field(default_factory=list)
    pre_aggregations: list[PreAggregation] = field(default_factory=list)
    grouping: list[str] = field(default_factory=list)
    sorting: list[dict[str, str]] = field(default_factory=list)
    limit: int = 100
    metrics: list[str] = field(default_factory=list)
    execution_strategy: ExecutionStrategy = "SEQUENTIAL"
    max_scan_rows: int = 5000

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_type": self.report_type,
            "board_id": self.board_id,
            "scan": self.scan.to_dict(),
            "filters": [f.to_dict() for f in self.filters],
            "pre_aggregations": [p.to_dict() for p in self.pre_aggregations],
            "grouping": list(self.grouping),
            "sorting": list(self.sorting),
            "limit": self.limit,
            "metrics": list(self.metrics),
            "execution_strategy": self.execution_strategy,
            "max_scan_rows": self.max_scan_rows,
        }


@dataclass
class OptimizedQueryPlan(QueryPlan):
    early_limit: bool = False
    filter_pushdown_order: list[str] = field(default_factory=list)
    parallel_dimensions: list[str] = field(default_factory=list)
    optimization_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "early_limit": self.early_limit,
                "filter_pushdown_order": list(self.filter_pushdown_order),
                "parallel_dimensions": list(self.parallel_dimensions),
                "optimization_notes": list(self.optimization_notes),
            }
        )
        return base
