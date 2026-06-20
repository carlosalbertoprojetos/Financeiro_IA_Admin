from __future__ import annotations

from typing import Any

from django.utils.dateparse import parse_datetime

from apps.integrations.core.canonical import CanonicalTask
from apps.integrations.models import CanonicalTaskRecord, IntegrationConnection


def canonical_task_from_payload(payload: dict[str, Any]) -> CanonicalTask:
    """Build a CanonicalTask from queue event payload (task.as_dict())."""
    due_raw = payload.get("due_date")
    due_date = None
    if due_raw:
        due_date = parse_datetime(str(due_raw).replace("Z", "+00:00"))

    return CanonicalTask(
        source_provider=payload["source_provider"],
        source_id=payload["source_id"],
        title=payload.get("title") or "(sem título)",
        status=payload.get("status") or "",
        project_id=payload.get("project_id") or "",
        due_date=due_date,
        metadata=payload.get("metadata") or {},
    )


def upsert_canonical_task(
    connection: IntegrationConnection,
    task: CanonicalTask,
) -> tuple[CanonicalTaskRecord, bool]:
    """
    Idempotent upsert keyed by (connection, source_provider, source_id).

    Safe to call multiple times for the same task event.
    """
    return CanonicalTaskRecord.objects.update_or_create(
        connection=connection,
        source_provider=task.source_provider,
        source_id=task.source_id,
        defaults={
            "title": task.title,
            "status": task.status,
            "due_date": task.due_date,
            "project_id": task.project_id,
            "metadata": task.metadata,
        },
    )
