from __future__ import annotations

from typing import Any

from django.db.models import Avg, Count, Sum

from apps.intelligence.models import BusinessValueRecordModel


def attribute_value(
    record: dict[str, Any],
    *,
    area: str = "",
    team: str = "",
    project: str = "",
    member: str = "",
    initiative: str = "",
    client: str = "",
) -> dict[str, Any]:
    """Attach attribution dimensions to a value record."""
    return {
        **record,
        "attribution": {
            "area": area or record.get("category", ""),
            "team": team,
            "project": project,
            "member": member,
            "initiative": initiative,
            "client": client,
        },
    }


def aggregate_by_dimension(
    dimension: str,
    *,
    board_id: str = "",
    days: int = 90,
) -> list[dict[str, Any]]:
    """Aggregate value records by area/team/project/member."""
    from django.utils import timezone
    from datetime import timedelta

    field_map = {
        "area": "category",
        "team": "team",
        "project": "project",
        "member": "member",
        "action": "action_type",
    }
    db_field = field_map.get(dimension, dimension)
    qs = BusinessValueRecordModel.objects.all()
    if board_id:
        qs = qs.filter(board_id=board_id)
    if days:
        qs = qs.filter(created_at__gte=timezone.now() - timedelta(days=days))

    rows = (
        qs.values(db_field)
        .annotate(
            total_avoided=Sum("avoided_loss"),
            total_cost=Sum("estimated_cost"),
            total_benefit=Sum("realized_benefit"),
            avg_roi=Avg("roi_pct"),
            count=Count("id"),
            avg_confidence=Avg("confidence_score"),
        )
        .order_by("-total_avoided")
    )

    return [
        {
            "dimension": dimension,
            "key": row[db_field] or "UNKNOWN",
            "avoided_loss": round(row["total_avoided"] or 0, 2),
            "estimated_cost": round(row["total_cost"] or 0, 2),
            "realized_benefit": round(row["total_benefit"] or 0, 2),
            "avg_roi_pct": round(row["avg_roi"] or 0, 1),
            "records": row["count"],
            "avg_confidence": round(row["avg_confidence"] or 0, 2),
        }
        for row in rows
    ]
