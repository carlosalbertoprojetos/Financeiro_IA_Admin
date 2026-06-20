from io import BytesIO
from typing import Any

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors


def throughput_chart(series: list[dict[str, Any]], *, width: float = 460, height: float = 180) -> Drawing:
    """Bar chart for throughput series."""
    drawing = Drawing(width, height)
    drawing.add(String(0, height - 12, "Throughput (cards concluídos)", fontSize=10, fillColor=colors.HexColor("#1F2937")))

    if not series:
        drawing.add(String(0, height / 2, "Sem dados de throughput", fontSize=9, fillColor=colors.grey))
        return drawing

    labels = [item.get("period", "") for item in series[:12]]
    values = [float(item.get("count", 0)) for item in series[:12]]

    chart = VerticalBarChart()
    chart.x = 20
    chart.y = 20
    chart.height = height - 50
    chart.width = width - 40
    chart.data = [values]
    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.angle = 30 if len(labels) > 4 else 0
    chart.categoryAxis.labels.boxAnchor = "ne"
    chart.categoryAxis.labels.fontSize = 7
    chart.valueAxis.valueMin = 0
    chart.bars[0].fillColor = colors.HexColor("#2563EB")
    chart.bars[0].strokeColor = colors.HexColor("#1D4ED8")
    drawing.add(chart)
    return drawing


def kpi_hours_chart(kpis: dict[str, Any], *, width: float = 460, height: float = 180) -> Drawing:
    """Bar chart comparing mean lead/cycle/aging hours."""
    drawing = Drawing(width, height)
    drawing.add(String(0, height - 12, "KPIs de tempo (média em horas)", fontSize=10, fillColor=colors.HexColor("#1F2937")))

    labels = ["Lead Time", "Cycle Time", "Aging"]
    values = [
        _summary_mean(kpis.get("lead_time")),
        _summary_mean(kpis.get("cycle_time")),
        _summary_mean(kpis.get("aging")),
    ]

    if not any(values):
        drawing.add(String(0, height / 2, "Sem KPIs de tempo disponíveis", fontSize=9, fillColor=colors.grey))
        return drawing

    chart = VerticalBarChart()
    chart.x = 20
    chart.y = 20
    chart.height = height - 50
    chart.width = width - 40
    chart.data = [values]
    chart.categoryAxis.categoryNames = labels
    chart.valueAxis.valueMin = 0
    chart.bars[0].fillColor = colors.HexColor("#059669")
    chart.bars[0].strokeColor = colors.HexColor("#047857")
    drawing.add(chart)
    return drawing


def rates_chart(kpis: dict[str, Any], *, width: float = 460, height: float = 180) -> Drawing:
    """Bar chart for delay and rework rates (%)."""
    drawing = Drawing(width, height)
    drawing.add(String(0, height - 12, "Taxas operacionais (%)", fontSize=10, fillColor=colors.HexColor("#1F2937")))

    delay_pct = _summary_value(kpis.get("delay_rate"), "delay_rate_pct")
    rework_pct = _summary_value(kpis.get("rework_rate"), "rework_rate_pct")
    labels = ["Delay Rate", "Rework Rate"]
    values = [delay_pct, rework_pct]

    chart = VerticalBarChart()
    chart.x = 20
    chart.y = 20
    chart.height = height - 50
    chart.width = width - 40
    chart.data = [values]
    chart.categoryAxis.categoryNames = labels
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max(100, max(values) * 1.2 if values else 100)
    chart.bars[0].fillColor = colors.HexColor("#DC2626")
    chart.bars[0].strokeColor = colors.HexColor("#B91C1C")
    drawing.add(chart)
    return drawing


def _summary_mean(kpi: dict[str, Any] | None) -> float:
    if not kpi:
        return 0.0
    summary = kpi.get("summary") or {}
    return float(summary.get("mean") or 0.0)


def _summary_value(kpi: dict[str, Any] | None, key: str) -> float:
    if not kpi:
        return 0.0
    summary = kpi.get("summary") or {}
    return float(summary.get(key) or 0.0)
