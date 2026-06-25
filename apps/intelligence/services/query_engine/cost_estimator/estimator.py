from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from apps.intelligence.services.query_engine.compiler.plan import OptimizedQueryPlan

RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
Recommendation = Literal["ALLOW", "OPTIMIZE", "REJECT"]

SOURCE_COST = {
    "timeline_events": 15,
    "cards": 10,
    "enriched_context": 25,
}


@dataclass
class CostEstimate:
    estimated_cost: int
    risk_level: RiskLevel
    recommendation: Recommendation
    estimated_rows: int
    number_of_filters: int
    grouping_complexity: int
    joins_required: int
    source_type_cost: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "estimated_cost": self.estimated_cost,
            "risk_level": self.risk_level,
            "recommendation": self.recommendation,
            "estimated_rows": self.estimated_rows,
            "number_of_filters": self.number_of_filters,
            "grouping_complexity": self.grouping_complexity,
            "joins_required": self.joins_required,
            "source_type_cost": self.source_type_cost,
        }


def estimate_cost(plan: OptimizedQueryPlan) -> CostEstimate:
    """Estimate query cost before execution. Does not execute data."""
    num_filters = len(plan.filters)
    grouping_complexity = len(plan.grouping) * (2 if plan.pre_aggregations else 1)
    joins_required = len(plan.scan.secondary_sources) + (1 if plan.scan.secondary_sources else 0)

    source_cost = SOURCE_COST.get(plan.scan.source, 10)
    for sec in plan.scan.secondary_sources:
        source_cost += SOURCE_COST.get(sec, 5)

    base_rows = plan.max_scan_rows
    filter_reduction = max(0.2, 1.0 - (num_filters * 0.12))
    estimated_rows = int(base_rows * filter_reduction)

    cost = 0
    cost += min(30, num_filters * 6)
    cost += min(20, grouping_complexity * 5)
    cost += min(25, joins_required * 8)
    cost += min(25, source_cost)
    if plan.execution_strategy == "PARALLEL":
        cost = int(cost * 0.85)
    if plan.early_limit:
        cost = int(cost * 0.75)
    if estimated_rows > 3000:
        cost += 15
    cost = min(100, max(0, cost))

    if cost >= 70:
        risk_level: RiskLevel = "HIGH"
    elif cost >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    if cost >= 85:
        recommendation: Recommendation = "REJECT"
    elif cost >= 55:
        recommendation = "OPTIMIZE"
    else:
        recommendation = "ALLOW"

    return CostEstimate(
        estimated_cost=cost,
        risk_level=risk_level,
        recommendation=recommendation,
        estimated_rows=estimated_rows,
        number_of_filters=num_filters,
        grouping_complexity=grouping_complexity,
        joins_required=joins_required,
        source_type_cost=source_cost,
    )
