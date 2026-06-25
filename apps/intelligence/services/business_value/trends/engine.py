from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.db.models import Avg, QuerySet, Sum
from django.db.models.functions import TruncMonth, TruncQuarter, TruncYear
from django.utils import timezone


def compute_value_trends(
    *,
    board_id: str = "",
    days: int = 365,
) -> dict[str, Any]:
    """Monthly, quarterly, and annual value trends from persisted records."""
    from apps.intelligence.models import BusinessValueRecordModel

    qs = BusinessValueRecordModel.objects.all()
    if board_id:
        qs = qs.filter(board_id=board_id)
    if days:
        qs = qs.filter(created_at__gte=timezone.now() - timedelta(days=days))

    return {
        "monthly": _trend_series(qs, TruncMonth("created_at"), "month"),
        "quarterly": _trend_series(qs, TruncQuarter("created_at"), "quarter"),
        "annual": _trend_series(qs, TruncYear("created_at"), "year"),
        "period_days": days,
    }


def _trend_series(qs: QuerySet, trunc_fn, label: str) -> list[dict[str, Any]]:
    rows = (
        qs.annotate(period=trunc_fn)
        .values("period")
        .annotate(
            avoided=Sum("avoided_loss"),
            cost=Sum("estimated_cost"),
            benefit=Sum("realized_benefit"),
            avg_roi=Avg("roi_pct"),
        )
        .order_by("period")
    )
    return [
        {
            "period": row["period"].isoformat() if row.get("period") else "",
            "label": label,
            "avoided_loss": round(row["avoided"] or 0, 2),
            "estimated_cost": round(row["cost"] or 0, 2),
            "realized_benefit": round(row["benefit"] or 0, 2),
            "avg_roi_pct": round(row["avg_roi"] or 0, 1),
        }
        for row in rows
    ]
