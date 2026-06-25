from __future__ import annotations

from typing import Any

from django.db.models import Avg, Count
from django.db.models.functions import TruncDate

from apps.intelligence.models import DecisionTraceRecord
from apps.intelligence.services.observability.config import is_debug_mode


def build_dashboard_stats(*, board_id: str = "", days: int = 7) -> dict[str, Any]:
    """Observability dashboard data — query flow, bottlenecks, errors."""
    qs = DecisionTraceRecord.objects.all()
    if board_id:
        qs = qs.filter(board_id=board_id)

    total = qs.count()
    errors = qs.filter(status="error").count()
    avg_ms = qs.aggregate(avg=Avg("execution_time_ms"))["avg"] or 0

    by_status = list(qs.values("status").annotate(count=Count("id")).order_by("-count"))
    slowest = list(
        qs.order_by("-execution_time_ms").values("trace_id", "query_id", "execution_time_ms", "status")[:10]
    )

    error_codes: dict[str, int] = {}
    for row in qs.filter(status="error").values_list("full_trace_json", flat=True)[:100]:
        for err in row.get("errors", []):
            code = err.get("code", "UNKNOWN")
            error_codes[code] = error_codes.get(code, 0) + 1

    frequent_rules: dict[str, int] = {}
    for row in qs.values_list("full_trace_json", flat=True)[:200]:
        for rule in row.get("rules_applied", []):
            key = rule.get("rule", "unknown")
            frequent_rules[key] = frequent_rules.get(key, 0) + 1

    ai_usage = sum(
        1 for row in qs.values_list("full_trace_json", flat=True)[:200]
        if row.get("ai_decisions")
    )

    return {
        "total_traces": total,
        "error_rate_pct": round(errors / max(total, 1) * 100, 1),
        "avg_execution_ms": round(avg_ms, 1),
        "by_status": by_status,
        "slowest_queries": slowest,
        "top_errors": sorted(error_codes.items(), key=lambda x: -x[1])[:10],
        "frequent_rules": sorted(frequent_rules.items(), key=lambda x: -x[1])[:10],
        "ai_decision_count": ai_usage,
        "debug_mode": is_debug_mode(),
    }


def build_insights_summary(*, limit: int = 20) -> list[dict[str, Any]]:
    """Recent AI/domain insights from traces."""
    rows = DecisionTraceRecord.objects.filter(status="success").order_by("-created_at")[:limit]
    insights: list[dict[str, Any]] = []
    for row in rows:
        ai = row.full_trace_json.get("ai_decisions", [])
        if ai:
            insights.append({
                "trace_id": row.trace_id,
                "query_id": row.query_id,
                "timestamp": row.created_at.isoformat(),
                "ai_decisions": ai,
            })
    return insights
