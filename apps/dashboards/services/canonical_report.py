"""Executive PDF payload from canonical Trello task records."""

from __future__ import annotations

from typing import Any

from apps.dashboards.services.canonical_metrics import build_canonical_dashboard


def _count_closed(tasks_by_status: list[dict[str, Any]]) -> int:
    closed_keywords = ("conclu", "done", "complete", "finaliz")
    closed = 0
    for row in tasks_by_status:
        status = (row.get("status") or "").lower()
        if any(keyword in status for keyword in closed_keywords):
            closed += row.get("count", 0)
    return closed


def build_canonical_report_metrics(
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
    total = dashboard["summary"]["total_tasks"]
    tasks_by_status = dashboard.get("tasks_by_status") or []
    completed = _count_closed(tasks_by_status)
    open_cards = max(total - completed, 0)
    trend = dashboard.get("trend_7d") or []

    overview = {
        "board_id": project_id or dashboard["filters"].get("project_id") or "trello",
        "generated_at": dashboard["generated_at"],
        "counts": {
            "total_cards": total,
            "open_cards": open_cards,
            "completed_cards": completed,
        },
        "kpis": {
            "throughput": {
                "summary": {"total_completed": completed},
                "series": [{"period": point["date"], "count": point["count"]} for point in trend],
            },
            "delay_rate": {
                "summary": {
                    "delay_rate_pct": round(
                        (dashboard["summary"]["overdue_count"] / total * 100) if total else 0,
                        2,
                    )
                }
            },
        },
    }

    return {
        "board_id": overview["board_id"],
        "generated_at": dashboard["generated_at"],
        "overview": overview,
        "dashboard": dashboard,
    }


def build_canonical_report_diagnosis(metrics: dict[str, Any]) -> dict[str, Any]:
    dashboard = metrics.get("dashboard") or {}
    summary = dashboard.get("summary") or {}
    total = summary.get("total_tasks", 0)
    overdue = summary.get("overdue_count", 0)

    if total == 0:
        return {
            "executive_summary": (
                "Não há tasks sincronizadas do Trello. "
                "Configure a integração e execute um sync antes de gerar o relatório."
            ),
            "problems": [],
            "risks": [],
            "recommendations": [
                {
                    "priority": "Alta",
                    "title": "Sincronizar Trello",
                    "action": "Conectar credenciais e executar sync do board.",
                    "expected_outcome": "Dados reais disponíveis para dashboard e relatórios.",
                }
            ],
        }

    problems = []
    if overdue:
        problems.append(
            {
                "title": "Tasks atrasadas",
                "severity": "alta" if overdue > 5 else "média",
                "description": f"{overdue} task(s) com prazo vencido no board sincronizado.",
            }
        )

    tasks_by_status = dashboard.get("tasks_by_status") or []
    if tasks_by_status:
        top = max(tasks_by_status, key=lambda row: row["count"])
        if top["count"] > total * 0.5:
            problems.append(
                {
                    "title": "Acúmulo operacional",
                    "severity": "média",
                    "description": (
                        f"{top['count']} tasks ({round(top['count']/total*100)}%) "
                        f"na lista «{top['status']}»."
                    ),
                }
            )

    risks = []
    if overdue and overdue / total > 0.15:
        risks.append(
            {
                "title": "Risco de atraso em entregas",
                "impact": "alto",
                "likelihood": "média",
                "description": "Proporção elevada de tasks vencidas no fluxo atual.",
            }
        )

    recommendations = [
        {
            "priority": "Alta" if overdue else "Média",
            "title": "Revisar tasks atrasadas",
            "action": "Priorizar cards vencidos e renegociar prazos no Trello.",
            "expected_outcome": "Redução do backlog crítico.",
        }
    ]

    return {
        "executive_summary": (
            f"Board com {total} tasks sincronizadas do Trello. "
            f"{overdue} atrasada(s). "
            f"Relatório gerado a partir dos dados canônicos do sync."
        ),
        "problems": problems,
        "risks": risks,
        "recommendations": recommendations,
    }
