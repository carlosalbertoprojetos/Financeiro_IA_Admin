"""Analytics derived from canonical Trello task records (portal layer)."""

from __future__ import annotations

from typing import Any

from apps.dashboards.services.canonical_metrics import build_canonical_dashboard


def _insights_from_dashboard(dashboard: dict[str, Any]) -> list[str]:
    insights: list[str] = []
    summary = dashboard.get("summary") or {}
    total = summary.get("total_tasks", 0)

    if total == 0:
        insights.append("Nenhuma task sincronizada. Conecte o Trello e execute um sync.")
        return insights

    overdue = summary.get("overdue_count", 0)
    if overdue:
        insights.append(f"{overdue} task(s) com prazo vencido.")

    tasks_by_status = dashboard.get("tasks_by_status") or []
    if tasks_by_status:
        top = max(tasks_by_status, key=lambda row: row["count"])
        insights.append(
            f"Maior concentração na lista/status «{top['status']}» ({top['count']} tasks)."
        )

    trend = dashboard.get("trend_7d") or []
    if len(trend) >= 2:
        recent = sum(point["count"] for point in trend[-3:])
        previous = sum(point["count"] for point in trend[:3])
        if recent > previous:
            insights.append("Atividade de atualização aumentou nos últimos dias.")
        elif recent < previous:
            insights.append("Atividade de atualização reduziu nos últimos dias.")

    overdue_items = (dashboard.get("overdue_tasks") or {}).get("items") or []
    if overdue_items:
        insights.append(f"Exemplo atrasado: «{overdue_items[0]['title']}».")

    return insights[:6]


def build_canonical_analytics(
    *,
    project_id: str | None = None,
    source_provider: str | None = "trello",
    connection_id: str | None = None,
) -> dict[str, Any]:
    dashboard = build_canonical_dashboard(
        project_id=project_id,
        source_provider=source_provider,
        connection_id=connection_id,
    )
    summary = dashboard["summary"]
    total = summary["total_tasks"]

    throughput_7d = sum(point["count"] for point in dashboard.get("trend_7d") or [])

    return {
        "endpoint": "dashboards/analytics",
        "generated_at": dashboard["generated_at"],
        "filters": dashboard["filters"],
        "summary": [
            {
                "id": "total_tasks",
                "label": "Total de tasks (Trello)",
                "value": str(total),
            },
            {
                "id": "overdue",
                "label": "Tasks atrasadas",
                "value": str(summary.get("overdue_count", 0)),
            },
            {
                "id": "throughput_7d",
                "label": "Atualizações (7 dias)",
                "value": str(throughput_7d),
            },
            {
                "id": "status_buckets",
                "label": "Listas/status distintos",
                "value": str(summary.get("status_buckets", 0)),
            },
        ],
        "tasks_by_status": dashboard.get("tasks_by_status") or [],
        "trend_7d": dashboard.get("trend_7d") or [],
        "overdue_tasks": dashboard.get("overdue_tasks") or {"count": 0, "items": []},
        "insights": _insights_from_dashboard(dashboard),
        "has_data": total > 0,
    }
