from io import BytesIO
from typing import Any

from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from reports.engine.charts import kpi_hours_chart, rates_chart, throughput_chart
from reports.exceptions import ReportValidationError


class DrawingFlowable(Flowable):
    """Embed a ReportLab Drawing in a Platypus story without renderPM."""

    def __init__(self, drawing: Drawing, width: float, height: float):
        super().__init__()
        self.drawing = drawing
        self.width = width
        self.height = height

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        self.drawing.drawOn(self.canv, 0, 0)


def build_executive_report_pdf(
    metrics: dict[str, Any],
    diagnosis: dict[str, Any],
    *,
    title: str = "Relatório Executivo Operacional",
    board_name: str | None = None,
) -> bytes:
    """
    Build an executive PDF from aggregated metrics and AI diagnosis.

    Returns PDF bytes.
    """
    overview = _extract_overview(metrics)
    _validate_diagnosis(diagnosis)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=title,
    )

    styles = _build_styles()
    story: list[Any] = []

    board_id = overview.get("board_id") or metrics.get("board_id") or "-"
    generated_at = overview.get("generated_at") or metrics.get("generated_at") or "-"
    display_name = board_name or board_id

    story.extend(_build_header(styles, title, display_name, generated_at))
    story.extend(_build_kpi_section(styles, overview))
    story.extend(_build_charts_section(styles, overview))
    story.extend(_build_diagnosis_section(styles, diagnosis))
    story.extend(_build_recommendations_section(styles, diagnosis))

    doc.build(story)
    return buffer.getvalue()


def _extract_overview(metrics: dict[str, Any]) -> dict[str, Any]:
    if "overview" in metrics and isinstance(metrics["overview"], dict):
        return metrics["overview"]
    if "kpis" in metrics:
        return metrics
    raise ReportValidationError("metrics must include overview or kpis")


def _validate_diagnosis(diagnosis: dict[str, Any]) -> None:
    required = ("executive_summary", "problems", "risks", "recommendations")
    for key in required:
        if key not in diagnosis:
            raise ReportValidationError(f"diagnosis missing required key: {key}")


def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#111827"),
            spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#4B5563"),
            spaceAfter=12,
        ),
        "section": ParagraphStyle(
            "ReportSection",
            parent=base["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1F2937"),
            spaceBefore=10,
            spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "ReportBody",
            parent=base["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#374151"),
            alignment=TA_LEFT,
            spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "ReportBullet",
            parent=base["Normal"],
            fontSize=10,
            leading=14,
            leftIndent=12,
            bulletIndent=0,
            textColor=colors.HexColor("#374151"),
            spaceAfter=4,
        ),
    }


def _build_header(
    styles: dict[str, ParagraphStyle],
    title: str,
    board_name: str,
    generated_at: str,
) -> list[Any]:
    return [
        Paragraph(title, styles["title"]),
        Paragraph(f"Board: <b>{board_name}</b>", styles["subtitle"]),
        Paragraph(f"Gerado em: {generated_at}", styles["subtitle"]),
        Spacer(1, 6 * mm),
    ]


def _build_kpi_section(styles: dict[str, ParagraphStyle], overview: dict[str, Any]) -> list[Any]:
    counts = overview.get("counts") or {}
    kpis = overview.get("kpis") or {}

    rows = [
        ["Indicador", "Valor"],
        ["Total de cards", str(counts.get("total_cards", 0))],
        ["Cards abertos", str(counts.get("open_cards", 0))],
        ["Cards concluídos", str(counts.get("completed_cards", 0))],
        ["Lead time médio (h)", _format_summary(kpis.get("lead_time"), "mean")],
        ["Cycle time médio (h)", _format_summary(kpis.get("cycle_time"), "mean")],
        ["Aging médio (h)", _format_summary(kpis.get("aging"), "mean")],
        ["Delay rate (%)", _format_summary(kpis.get("delay_rate"), "delay_rate_pct")],
        ["Rework rate (%)", _format_summary(kpis.get("rework_rate"), "rework_rate_pct")],
        ["Throughput total", _format_summary(kpis.get("throughput"), "total_completed")],
    ]

    table = Table(rows, colWidths=[80 * mm, 90 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    return [
        Paragraph("KPIs", styles["section"]),
        table,
        Spacer(1, 8 * mm),
    ]


def _build_charts_section(styles: dict[str, ParagraphStyle], overview: dict[str, Any]) -> list[Any]:
    kpis = overview.get("kpis") or {}
    throughput_series = (kpis.get("throughput") or {}).get("series") or []

    charts = [
        throughput_chart(throughput_series),
        kpi_hours_chart(kpis),
        rates_chart(kpis),
    ]

    story: list[Any] = [Paragraph("Gráficos", styles["section"])]
    for chart in charts:
        story.append(DrawingFlowable(chart, chart.width, chart.height))
        story.append(Spacer(1, 4 * mm))

    story.append(Spacer(1, 4 * mm))
    return story


def _build_diagnosis_section(styles: dict[str, ParagraphStyle], diagnosis: dict[str, Any]) -> list[Any]:
    story = [
        PageBreak(),
        Paragraph("Diagnóstico", styles["section"]),
        Paragraph("<b>Resumo executivo</b>", styles["body"]),
        Paragraph(diagnosis.get("executive_summary", ""), styles["body"]),
        Spacer(1, 4 * mm),
        Paragraph("<b>Problemas identificados</b>", styles["body"]),
    ]

    problems = diagnosis.get("problems") or []
    if not problems:
        story.append(Paragraph("Nenhum problema destacado.", styles["body"]))
    else:
        for problem in problems[:8]:
            story.append(
                Paragraph(
                    f"• <b>{problem.get('title', 'Problema')}</b> "
                    f"({problem.get('severity', 'n/a')}): {problem.get('description', '')}",
                    styles["bullet"],
                )
            )

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("<b>Riscos</b>", styles["body"]))

    risks = diagnosis.get("risks") or []
    if not risks:
        story.append(Paragraph("Nenhum risco destacado.", styles["body"]))
    else:
        for risk in risks[:8]:
            story.append(
                Paragraph(
                    f"• <b>{risk.get('title', 'Risco')}</b> "
                    f"(impacto: {risk.get('impact', 'n/a')}, "
                    f"probabilidade: {risk.get('likelihood', 'n/a')}): "
                    f"{risk.get('description', '')}",
                    styles["bullet"],
                )
            )

    story.append(Spacer(1, 6 * mm))
    return story


def _build_recommendations_section(styles: dict[str, ParagraphStyle], diagnosis: dict[str, Any]) -> list[Any]:
    story = [Paragraph("Recomendações", styles["section"])]
    recommendations = diagnosis.get("recommendations") or []

    if not recommendations:
        story.append(Paragraph("Nenhuma recomendação disponível.", styles["body"]))
        return story

    rows = [["Prioridade", "Recomendação", "Ação", "Resultado esperado"]]
    for item in recommendations[:10]:
        rows.append(
            [
                item.get("priority", "-"),
                item.get("title", "-"),
                item.get("action", "-"),
                item.get("expected_outcome", "-"),
            ]
        )

    table = Table(rows, colWidths=[22 * mm, 38 * mm, 55 * mm, 55 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    story.append(table)
    return story


def _format_summary(kpi: dict[str, Any] | None, key: str) -> str:
    if not kpi:
        return "-"
    summary = kpi.get("summary") or {}
    value = summary.get(key)
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)
