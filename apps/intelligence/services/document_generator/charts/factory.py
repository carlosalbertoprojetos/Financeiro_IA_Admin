from __future__ import annotations

from typing import Any

from apps.intelligence.services.document_generator.presentation import ChartModel


def build_chart_specs(output_contract: dict[str, Any]) -> list[ChartModel]:
    tables = output_contract.get("executive_tables", {})
    rankings = output_contract.get("rankings", {})
    charts: list[ChartModel] = []

    categories = tables.get("top_categorias", [])
    if categories:
        charts.append(
            ChartModel(
                title="Top categorias",
                chart_type="bar",
                labels=[str(item.get("categoria")) for item in categories[:8]],
                values=[float(item.get("quantidade") or 0) for item in categories[:8]],
                source="executive_tables.top_categorias",
            )
        )

    members = tables.get("top_membros", [])
    if members:
        charts.append(
            ChartModel(
                title="Carga por membro",
                chart_type="distribution",
                labels=[str(item.get("membro")) for item in members[:8]],
                values=[float(item.get("cards") or 0) for item in members[:8]],
                source="executive_tables.top_membros",
            )
        )

    risks = rankings.get("top_10_risks", [])
    if risks:
        charts.append(
            ChartModel(
                title="Ranking de riscos",
                chart_type="ranking",
                labels=[str(item.get("title")) for item in risks[:8]],
                values=[float(item.get("score") or item.get("rank") or 0) for item in risks[:8]],
                source="rankings.top_10_risks",
            )
        )

    timeline = output_contract.get("analytical_appendix", {}).get("timeline", {})
    monthly = timeline.get("created_by_month") if isinstance(timeline, dict) else []
    if monthly:
        charts.append(
            ChartModel(
                title="Timeline",
                chart_type="timeline",
                labels=[str(item.get("name")) for item in monthly[:12]],
                values=[float(item.get("count") or 0) for item in monthly[:12]],
                source="analytical_appendix.timeline.created_by_month",
            )
        )
    return charts
