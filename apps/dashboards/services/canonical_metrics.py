from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from django.db.models import Count, Q, QuerySet
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.integrations.models import CanonicalTaskRecord

EMPTY_STATUS_LABEL = "(sem status)"


def _base_queryset(
    *,
    project_id: str | None = None,
    source_provider: str | None = None,
    connection_id: str | None = None,
) -> QuerySet[CanonicalTaskRecord]:
    queryset = CanonicalTaskRecord.objects.all()
    if connection_id:
        queryset = queryset.filter(connection_id=connection_id)
    elif project_id:
        queryset = queryset.filter(project_id=project_id)
    if source_provider:
        queryset = queryset.filter(source_provider=source_provider)
    return queryset


def _tasks_by_status(queryset: QuerySet[CanonicalTaskRecord]) -> list[dict[str, Any]]:
    rows = (
        queryset.values("status")
        .annotate(count=Count("id"))
        .order_by("-count", "status")
    )
    return [
        {
            "status": row["status"] or EMPTY_STATUS_LABEL,
            "count": row["count"],
        }
        for row in rows
    ]


def _overdue_tasks(
    queryset: QuerySet[CanonicalTaskRecord],
    *,
    reference_time,
    limit: int = 20,
) -> dict[str, Any]:
    overdue_queryset = (
        queryset.filter(due_date__isnull=False, due_date__lt=reference_time)
        .exclude(metadata__contains={"closed": True})
        .order_by("due_date")
    )

    items = [
        {
            "source_id": task.source_id,
            "title": task.title,
            "status": task.status or EMPTY_STATUS_LABEL,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "source_provider": task.source_provider,
            "project_id": task.project_id,
        }
        for task in overdue_queryset[:limit]
    ]

    return {
        "count": overdue_queryset.count(),
        "items": items,
    }


def _by_source_provider(queryset: QuerySet[CanonicalTaskRecord]) -> list[dict[str, Any]]:
    rows = (
        queryset.values("source_provider")
        .annotate(count=Count("id"))
        .order_by("-count", "source_provider")
    )
    return [{"source_provider": row["source_provider"], "count": row["count"]} for row in rows]


def _trend_last_7_days(
    queryset: QuerySet[CanonicalTaskRecord],
    *,
    reference_time,
) -> list[dict[str, Any]]:
    start_day = (reference_time - timedelta(days=6)).date()
    end_day = reference_time.date()

    daily_counts = {
        row["day"]: row["count"]
        for row in (
            queryset.filter(updated_at__date__gte=start_day, updated_at__date__lte=end_day)
            .annotate(day=TruncDate("updated_at"))
            .values("day")
            .annotate(count=Count("id"))
        )
    }

    trend: list[dict[str, Any]] = []
    current: date = start_day
    while current <= end_day:
        trend.append(
            {
                "date": current.isoformat(),
                "count": daily_counts.get(current, 0),
            }
        )
        current += timedelta(days=1)
    return trend


def build_canonical_dashboard(
    *,
    project_id: str | None = None,
    source_provider: str | None = None,
    connection_id: str | None = None,
    reference_time=None,
) -> dict[str, Any]:
    now = reference_time or timezone.now()
    queryset = _base_queryset(
        project_id=project_id,
        source_provider=source_provider,
        connection_id=connection_id,
    )

    overdue = _overdue_tasks(queryset, reference_time=now)
    tasks_by_status = _tasks_by_status(queryset)
    by_provider = _by_source_provider(queryset)
    trend_7d = _trend_last_7_days(queryset, reference_time=now)

    return {
        "endpoint": "dashboards/metrics",
        "generated_at": now.isoformat(),
        "filters": {
            "project_id": project_id or None,
            "source_provider": source_provider or None,
            "connection_id": connection_id or None,
        },
        "summary": {
            "total_tasks": queryset.count(),
            "overdue_count": overdue["count"],
            "status_buckets": len(tasks_by_status),
            "source_providers": len(by_provider),
        },
        "tasks_by_status": tasks_by_status,
        "overdue_tasks": overdue,
        "by_source_provider": by_provider,
        "trend_7d": trend_7d,
    }
