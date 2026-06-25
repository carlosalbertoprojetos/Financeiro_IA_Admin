from __future__ import annotations

from collections import defaultdict
from typing import Any

from django.db.models import Avg, Count, Q

from apps.intelligence.models import DecisionEffectivenessRecord
from apps.intelligence.services.organizational_learning.outcomes.evaluator import OUTCOME_SUCCESS


def analyze_action_patterns(*, board_id: str = "", months: int = 12) -> dict[str, Any]:
    """Detect effective/ineffective actions from historical records."""
    qs = DecisionEffectivenessRecord.objects.all()
    if board_id:
        qs = qs.filter(board_id=board_id)

    by_action: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "count": 0,
        "success_count": 0,
        "avg_effectiveness": 0.0,
        "avg_risk_reduction_pct": 0.0,
        "avg_sla_improvement_pct": 0.0,
    })

    for row in qs:
        stats = by_action[row.action_type]
        stats["count"] += 1
        if row.outcome_label == OUTCOME_SUCCESS:
            stats["success_count"] += 1

    aggregates = qs.values("action_type").annotate(
        avg_eff=Avg("effectiveness_score"),
        avg_risk_red=Avg("risk_before") - Avg("risk_after"),
        count=Count("id"),
        success=Count("id", filter=Q(outcome_label=OUTCOME_SUCCESS)),
    )

    action_stats: list[dict[str, Any]] = []
    for agg in aggregates:
        total = agg["count"] or 1
        success_rate = round((agg["success"] / total) * 100, 1)
        avg_risk_before = qs.filter(action_type=agg["action_type"]).aggregate(a=Avg("risk_before"))["a"] or 0
        avg_risk_after = qs.filter(action_type=agg["action_type"]).aggregate(a=Avg("risk_after"))["a"] or 0
        risk_red_pct = round(((avg_risk_before - avg_risk_after) / avg_risk_before * 100), 1) if avg_risk_before else 0

        action_stats.append({
            "action_type": agg["action_type"],
            "executions": total,
            "success_rate_pct": success_rate,
            "avg_effectiveness": round(agg["avg_eff"] or 0, 1),
            "avg_risk_reduction_pct": risk_red_pct,
        })

    action_stats.sort(key=lambda x: x["avg_effectiveness"], reverse=True)

    most_effective = action_stats[:5]
    least_effective = sorted(action_stats, key=lambda x: x["avg_effectiveness"])[:5]

    combinations = _analyze_combinations(qs)

    return {
        "period_months": months,
        "board_id": board_id or "all",
        "most_effective_actions": most_effective,
        "least_effective_actions": least_effective,
        "action_combinations": combinations,
        "total_records": qs.count(),
    }


def _analyze_combinations(qs) -> list[dict[str, Any]]:
    """Find recurring category + action_type patterns."""
    combos: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "success": 0, "avg_eff": 0.0})
    for row in qs:
        key = f"{row.category or 'GENERAL'}|{row.action_type}"
        combos[key]["count"] += 1
        if row.outcome_label == OUTCOME_SUCCESS:
            combos[key]["success"] += 1
        combos[key]["avg_eff"] += row.effectiveness_score

    results = []
    for key, stats in combos.items():
        category, action_type = key.split("|", 1)
        count = stats["count"]
        results.append({
            "category": category,
            "action_type": action_type,
            "occurrences": count,
            "success_rate_pct": round((stats["success"] / count) * 100, 1) if count else 0,
            "avg_effectiveness": round(stats["avg_eff"] / count, 1) if count else 0,
        })
    return sorted(results, key=lambda x: x["avg_effectiveness"], reverse=True)[:10]


def get_action_historical_stats(
    action_type: str,
    *,
    category: str = "",
    board_id: str = "",
) -> dict[str, Any]:
    """Historical effectiveness for a single action type — used by recommendation evolution."""
    qs = DecisionEffectivenessRecord.objects.filter(action_type=action_type)
    if category:
        qs = qs.filter(category__iexact=category)
    if board_id:
        qs = qs.filter(board_id=board_id)

    total = qs.count()
    if total == 0:
        return {
            "action_type": action_type,
            "sample_size": 0,
            "success_rate_pct": None,
            "avg_risk_reduction_pct": None,
            "avg_effectiveness": None,
        }

    success = qs.filter(outcome_label=OUTCOME_SUCCESS).count()
    avg_before = qs.aggregate(v=Avg("risk_before"))["v"] or 0
    avg_after = qs.aggregate(v=Avg("risk_after"))["v"] or 0
    avg_sla_before = qs.aggregate(v=Avg("sla_before"))["v"] or 0
    avg_sla_after = qs.aggregate(v=Avg("sla_after"))["v"] or 0

    risk_red = round(((avg_before - avg_after) / avg_before * 100), 1) if avg_before else 0
    sla_imp = round(((avg_sla_before - avg_sla_after) / avg_sla_before * 100), 1) if avg_sla_before else 0

    return {
        "action_type": action_type,
        "category": category or "all",
        "sample_size": total,
        "success_rate_pct": round((success / total) * 100, 1),
        "avg_risk_reduction_pct": risk_red,
        "avg_sla_improvement_pct": sla_imp,
        "avg_effectiveness": round(qs.aggregate(v=Avg("effectiveness_score"))["v"] or 0, 1),
    }
