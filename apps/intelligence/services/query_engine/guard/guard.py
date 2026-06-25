from __future__ import annotations

from apps.intelligence.services.eql.errors import (
    MissingLimitError,
    QueryCostRejectedError,
    QueryGuardRejectedError,
)
from apps.intelligence.services.query_engine.compiler.plan import OptimizedQueryPlan
from apps.intelligence.services.query_engine.cost_estimator.estimator import CostEstimate


def guard_query(plan: OptimizedQueryPlan, cost: CostEstimate) -> None:
    """
    Protect the system from dangerous queries.
    Does not execute data — only validates plan + cost.
    """
    if not plan.limit or plan.limit <= 0:
        raise MissingLimitError("LIMIT is required for all queries")

    if plan.grouping and (not plan.limit or plan.limit > 500):
        raise QueryGuardRejectedError(
            "GROUP BY requires an explicit LIMIT of 500 or less",
            code="GROUP_BY_WITHOUT_LIMIT",
        )

    has_period = any(f.field == "period" for f in plan.filters)
    if plan.filters and not has_period:
        raise QueryGuardRejectedError(
            "Queries with filters must include a temporal scope (PERIOD filter)",
            code="MISSING_TEMPORAL_SCOPE",
        )

    if cost.estimated_cost > 85 or cost.recommendation == "REJECT":
        raise QueryCostRejectedError(
            f"Query cost {cost.estimated_cost} exceeds maximum allowed (85)",
            code="COST_TOO_HIGH",
        )
