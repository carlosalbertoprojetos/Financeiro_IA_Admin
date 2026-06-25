from __future__ import annotations

from typing import Any


def build_query_lineage(
    *,
    query_raw: str,
    ast: dict[str, Any],
    query_plan: dict[str, Any] | None = None,
    optimized_plan: dict[str, Any] | None = None,
    cost_estimate: dict[str, Any] | None = None,
    governance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Track EQL → AST → Query Plan → Optimized Plan → Execution Path."""
    return {
        "eql_original": query_raw[:5000],
        "ast": ast,
        "query_plan": query_plan or {},
        "optimized_plan": optimized_plan or {},
        "execution_path": _execution_path(optimized_plan),
        "cost_estimate": cost_estimate or {},
        "governance": governance or {},
        "semantic_filters": ast.get("semantic_filters", {}),
    }


def _execution_path(optimized_plan: dict[str, Any] | None) -> list[str]:
    if not optimized_plan:
        return []
    path = [f"scan:{optimized_plan.get('scan', {}).get('source', 'cards')}"]
    path.extend(f"filter:{f}" for f in optimized_plan.get("filter_pushdown_order", []))
    if optimized_plan.get("early_limit"):
        path.append("early_limit")
    if optimized_plan.get("execution_strategy") == "PARALLEL":
        path.append("parallel_execution")
    for dim in optimized_plan.get("grouping", []):
        path.append(f"group:{dim}")
    return path
