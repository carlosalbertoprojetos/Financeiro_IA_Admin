from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.intelligence.services.document_generator.presentation import PresentationModel


def build_executive_pdf(model: PresentationModel) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="EDGTitle", fontSize=22, leading=28, textColor=colors.HexColor(model.theme.primary_color), spaceAfter=18))
    styles.add(ParagraphStyle(name="EDGSection", fontSize=14, leading=18, textColor=colors.HexColor(model.theme.primary_color), spaceBefore=14, spaceAfter=8))
    styles.add(ParagraphStyle(name="EDGBody", fontSize=9, leading=12, textColor=colors.HexColor(model.theme.text_color)))
    story = [
        Paragraph(model.title, styles["EDGTitle"]),
        Paragraph(model.subtitle, styles["EDGBody"]),
        Paragraph(model.branding.confidentiality, styles["EDGBody"]),
        Spacer(1, 20),
        Paragraph("Sumario", styles["EDGSection"]),
        *_bullets(model.sections, styles["EDGBody"]),
        PageBreak(),
        Paragraph("Executive Brief", styles["EDGSection"]),
        Paragraph(model.executive_brief.get("summary", ""), styles["EDGBody"]),
        _kpi_cards(model),
        Paragraph("Scorecard", styles["EDGSection"]),
        Paragraph(f"Score operacional: {model.scorecard.get('score_operacional', 'N/A')}", styles["EDGBody"]),
        Paragraph("KPIs", styles["EDGSection"]),
        _table_from_rows(["Metrica", "Valor", "Status", "Interpretacao"], model.tables.get("kpis_principais", []), ["metrica", "valor", "status", "interpretacao"]),
        Paragraph("Top Drivers", styles["EDGSection"]),
        *_bullets([item.get("title") for item in model.rankings.get("top_10_causes", [])[:3]], styles["EDGBody"]),
        Paragraph("Diagnostico", styles["EDGSection"]),
        _table_from_rows(["Categoria", "Qtd", "Risco", "Acao"], model.tables.get("top_categorias", []), ["categoria", "quantidade", "risco", "acao"]),
        Paragraph("Riscos", styles["EDGSection"]),
        _table_from_rows(["Risco", "Score", "Acao"], model.risks, ["title", "score", "recommended_action"]),
        Paragraph("Decisoes", styles["EDGSection"]),
        _table_from_rows(["Decisao", "Evidencia", "Urgencia", "Dono"], model.decisions, ["decisao", "evidencia", "urgencia", "dono_sugerido"]),
        Paragraph("Plano de Acao", styles["EDGSection"]),
        _table_from_rows(["Acao", "Dono", "Prazo", "Resultado"], model.action_plan, ["acao", "dono", "prazo", "resultado_esperado"]),
        Paragraph("Rankings", styles["EDGSection"]),
        *_ranking_blocks(model, styles["EDGBody"]),
        Paragraph("Evidencias", styles["EDGSection"]),
        *_bullets([item.get("evidence") or item.get("claim") for item in model.evidence[:20]], styles["EDGBody"]),
        Paragraph("Anexos", styles["EDGSection"]),
        Paragraph(f"Cards no anexo: {len(model.appendix.get('dados_por_card', []))}", styles["EDGBody"]),
    ]
    document.build(story, onFirstPage=_decorate_page(model), onLaterPages=_decorate_page(model))
    return buffer.getvalue()


def _decorate_page(model: PresentationModel):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor(model.theme.primary_color))
        canvas.rect(0, A4[1] - 32, A4[0], 32, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(42, A4[1] - 20, model.branding.header)
        canvas.setFillColor(colors.HexColor(model.theme.muted_color))
        canvas.drawString(42, 24, model.branding.footer)
        canvas.drawRightString(A4[0] - 42, 24, f"Pagina {doc.page}")
        canvas.restoreState()

    return draw


def _kpi_cards(model: PresentationModel) -> Table:
    data = [[item.get("metrica", ""), str(item.get("valor", ""))] for item in model.kpis[:5]]
    table = Table(data, colWidths=[5 * cm, 3 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E5E7EB")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(model.theme.secondary_color)),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.white),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ]
        )
    )
    return table


def _table_from_rows(headers: list[str], rows: list[dict], keys: list[str]) -> Table:
    data = [headers]
    for row in rows[:12]:
        data.append([_cell(row.get(key, "")) for key in keys])
    if len(data) == 1:
        data.append(["Sem dados"] + [""] * (len(headers) - 1))
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def _bullets(items: list, style) -> list[Paragraph]:
    return [Paragraph(f"- {_cell(item)}", style) for item in items if item]


def _ranking_blocks(model: PresentationModel, style) -> list[Paragraph]:
    blocks = []
    for title, rows in model.rankings.items():
        blocks.append(Paragraph(title, style))
        blocks.extend(_bullets([row.get("name") or row.get("title") or row.get("card_id") for row in rows[:5]], style))
    return blocks


def _cell(value: object) -> str:
    if isinstance(value, list):
        return "; ".join(map(str, value[:3]))
    if isinstance(value, dict):
        return str(value.get("title") or value.get("evidence") or value)
    return str(value if value is not None else "")[:180]
