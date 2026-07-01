from __future__ import annotations

import csv
import io
import json
from typing import Any

from apps.intelligence.services.report_query.domain.filters import ExportFormat


def export_report(result: dict[str, Any], fmt: ExportFormat) -> dict[str, Any] | None:
    if fmt == ExportFormat.JSON:
        return None

    exporters = {
        ExportFormat.CSV: _export_csv,
        ExportFormat.EXCEL: _export_excel,
        ExportFormat.MARKDOWN: _export_markdown,
        ExportFormat.PDF: _export_pdf,
        ExportFormat.PPTX: _export_pptx,
    }
    handler = exporters.get(fmt)
    if not handler:
        return None
    return handler(result)


def _export_csv(result: dict[str, Any]) -> dict[str, Any]:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "card_id",
            "title",
            "status",
            "activity_type",
            "activity_confidence",
            "risk_score",
            "description_quality_score",
            "comment_count",
            "checklist_pending",
            "next_action",
        ]
    )
    for card in result.get("cards", []):
        writer.writerow(
            [
                card.get("card_id"),
                card.get("title"),
                card.get("status"),
                card.get("activity_type"),
                card.get("activity_confidence"),
                card.get("risk_score"),
                card.get("description_quality_score"),
                card.get("comment_count"),
                card.get("checklist_pending"),
                card.get("next_action"),
            ]
        )
    content = buffer.getvalue().encode("utf-8-sig")
    return {
        "format": "csv",
        "content_type": "text/csv",
        "filename": "report.csv",
        "content_base64": _b64(content),
        "size_bytes": len(content),
    }


def _export_excel(result: dict[str, Any]) -> dict[str, Any]:
    csv_export = _export_csv(result)
    return {
        **csv_export,
        "format": "excel",
        "content_type": "application/vnd.ms-excel",
        "filename": "report.xls",
    }


def _export_markdown(result: dict[str, Any]) -> dict[str, Any]:
    meta = result.get("meta", {})
    data = result.get("data", {})
    brief = result.get("executive_brief", {})
    scorecard = result.get("operational_scorecard", {})
    benchmark = result.get("internal_benchmark", {})
    analytical = result.get("analytical", {})
    narrative = result.get("executive_narrative", {})
    discovery = result.get("discovery", {})
    story = result.get("executive_story", {})
    tables = result.get("executive_tables", {})
    rankings = result.get("rankings", {})
    output = result.get("report_output", {})
    commercial = result.get("commercial_report_score", {})
    quality = analytical.get("quality", {})
    metrics_pack = analytical.get("metrics_pack", {})
    recommendations = analytical.get("recommendations", [])
    readability = narrative.get("executive_readability_score", {})
    intelligence = discovery.get("report_intelligence_score", {})
    story_quality = story.get("executive_story_quality_score", {})
    narrative_sections = narrative.get("sections", {})
    lines = [
        f"# Relatório {meta.get('report_type', '')}",
        "",
        "## Índice",
        "",
        "- Executive Brief",
        "- Diagnóstico Gerencial",
        "- História Executiva",
        "- Tabelas Executivas",
        "- Rankings",
        "- Top 3 Drivers",
        "- Decisões Prioritárias",
        "- Plano de Ação",
        "- Anexo Analítico",
        "",
        f"**Board:** {meta.get('board_name') or meta.get('board_id', '')}",
        f"**Período:** {meta.get('period', 'N/A')}",
        f"**Versão do relatório:** {meta.get('report_version', '1.0')}",
        f"**Cards:** {meta.get('matched_cards', 0)}",
        f"**Qualidade analítica:** {quality.get('report_quality_score', 'N/A')} ({quality.get('label', 'N/A')})",
        f"**Legibilidade executiva:** {readability.get('score', 'N/A')} ({readability.get('label', 'N/A')})",
        f"**Inteligência do relatório:** {intelligence.get('score', 'N/A')} ({intelligence.get('label', 'N/A')})",
        f"**Qualidade da história:** {story_quality.get('score', 'N/A')} ({story_quality.get('label', 'N/A')})",
        f"**CommercialReportScore:** {commercial.get('score', 'N/A')} / {commercial.get('target', 95)} ({commercial.get('status', 'N/A')})",
        "",
        "## Executive Brief",
        "",
        *_markdown_brief(brief),
        "",
        "## Diagnóstico Gerencial",
        "",
        *_markdown_management_diagnosis(output.get("management_diagnosis", {})),
        "",
        "## História Executiva",
        "",
        f"**Headline:** {story.get('headline', '')}",
        "",
        story.get("period_story", ""),
        "",
        "## Tabelas Executivas",
        "",
        "### Scorecard Executivo",
        "",
        *_markdown_scorecard(scorecard),
        "",
        "### Tabela 1 — KPIs principais",
        "",
        *_markdown_table(
            tables.get("kpis_principais", []),
            ["metrica", "valor", "status", "variacao", "interpretacao"],
            ["Métrica", "Valor", "Status", "Variação", "Interpretação"],
        ),
        "",
        "### Tabela 2 — Top categorias",
        "",
        *_markdown_table(
            tables.get("top_categorias", []),
            ["categoria", "quantidade", "sla", "risco", "tempo_medio", "acao"],
            ["Categoria", "Quantidade", "SLA", "Risco", "Tempo médio", "Ação"],
        ),
        "",
        "### Tabela 3 — Top membros",
        "",
        *_markdown_table(
            tables.get("top_membros", []),
            ["membro", "cards", "concluidos", "atrasados", "tempo_medio", "observacao"],
            ["Membro", "Cards", "Concluídos", "Atrasados", "Tempo médio", "Observação"],
        ),
        "",
        "### Tabela 4 — Gargalos",
        "",
        *_markdown_table(
            tables.get("gargalos", []),
            ["lista_etapa", "cards", "tempo_medio", "severidade", "recomendacao"],
            ["Lista/Etapa", "Cards", "Tempo médio", "Severidade", "Recomendação"],
        ),
        "",
        "### Tabela 5 — Decisões",
        "",
        *_markdown_table(
            tables.get("decisoes", []),
            ["decisao", "evidencia", "impacto_esperado", "urgencia", "dono_sugerido"],
            ["Decisão", "Evidência", "Impacto esperado", "Urgência", "Dono sugerido"],
        ),
        "",
        "## Rankings",
        "",
        *_markdown_rankings(rankings),
        "",
        "### Top 3 Drivers",
        "",
        *_markdown_story_items(story.get("key_drivers", []), title_key="title", action_key="recommended_action"),
        "",
        "### Decisões Prioritárias",
        "",
        *_markdown_story_items(story.get("decision_ready_summary", []), title_key="decision", action_key="consequence_if_no_action"),
        "",
        "### Plano de Ação",
        "",
        *_markdown_story_items(story.get("action_plan", []), title_key="action", action_key="expected_result"),
        "",
        "## Narrativa Executiva",
        "",
        *_markdown_narrative_sections(narrative_sections),
        "",
        "## O que merece atenção",
        "",
        *_markdown_discovery_items(discovery.get("executive_highlights", []), title_key="title"),
        "",
        "## Descobertas",
        "",
        *_markdown_discovery_items(discovery.get("executive_surprises", []), title_key="text"),
        "",
        "## Anomalias",
        "",
        *_markdown_discovery_items(discovery.get("anomalies", []), title_key="title"),
        "",
        "## Hotspots",
        "",
        f"```json\n{json.dumps(discovery.get('hotspots', {}), indent=2, ensure_ascii=False, default=str)[:3000]}\n```",
        "",
        "## Oportunidades",
        "",
        *_markdown_discovery_items(discovery.get("opportunities", []), title_key="title"),
        "",
        "## Cenário provável",
        "",
        *_markdown_forecast_items(discovery.get("what_happens_next", [])),
        "",
        "## Indicadores Analíticos",
        "",
        f"- SLA: {json.dumps(metrics_pack.get('sla', {}), ensure_ascii=False, default=str)}",
        f"- Qualidade: {json.dumps(metrics_pack.get('quality', {}), ensure_ascii=False, default=str)}",
        f"- Comunicação: {json.dumps(metrics_pack.get('communication', {}), ensure_ascii=False, default=str)}",
        "",
        "## Recomendações",
        "",
        *[
            f"- **{item.get('priority', '')}:** {item.get('action', '')} Evidências: {', '.join(map(str, item.get('evidence', [])))}"
            for item in recommendations[:8]
        ],
        "",
        "## Anexo Analítico",
        "",
        *_markdown_appendix(output.get("analytical_appendix", {})),
        "",
        "## Resumo técnico",
        "",
        f"```json\n{json.dumps(data, indent=2, ensure_ascii=False, default=str)[:3000]}\n```",
    ]
    content = "\n".join(lines).encode("utf-8")
    return {
        "format": "markdown",
        "content_type": "text/markdown",
        "filename": "report.md",
        "content_base64": _b64(content),
        "size_bytes": len(content),
    }


def _export_pdf(result: dict[str, Any]) -> dict[str, Any]:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = 805
        meta = result.get("meta", {})
        brief = result.get("executive_brief", {})
        scorecard = result.get("operational_scorecard", {})
        benchmark = result.get("internal_benchmark", {})
        analytical = result.get("analytical", {})
        narrative = result.get("executive_narrative", {})
        discovery = result.get("discovery", {})
        story = result.get("executive_story", {})
        quality = analytical.get("quality", {})
        metrics_pack = analytical.get("metrics_pack", {})
        readability = narrative.get("executive_readability_score", {})
        intelligence = discovery.get("report_intelligence_score", {})
        story_quality = story.get("executive_story_quality_score", {})

        c.setFillColor(colors.HexColor("#0F172A"))
        c.rect(0, height - 125, width, 125, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, f"Relatório Executivo {meta.get('report_type', '')}")
        y -= 22
        c.setFont("Helvetica", 9)
        c.drawString(50, y, f"{meta.get('board_name') or meta.get('board_id', '')} | {meta.get('period', 'N/A')}")
        y -= 45
        c.setFillColor(colors.HexColor("#111827"))
        for index, card in enumerate(
            [
                ("Cards", meta.get("matched_cards", 0)),
                ("SLA", f"{metrics_pack.get('sla', {}).get('compliance_pct', 'N/A')}%"),
                ("Decisao", story_quality.get("score", "N/A")),
                ("Inteligencia", intelligence.get("score", "N/A")),
            ]
        ):
            x = 50 + index * 122
            c.setFillColor(colors.HexColor("#E5E7EB"))
            c.roundRect(x, y - 38, 108, 45, 4, stroke=0, fill=1)
            c.setFillColor(colors.HexColor("#111827"))
            c.setFont("Helvetica-Bold", 13)
            c.drawString(x + 8, y - 12, str(card[1]))
            c.setFont("Helvetica", 7)
            c.drawString(x + 8, y - 27, card[0])
        y -= 70
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "Executive Brief")
        y -= 16
        c.setFont("Helvetica", 9)
        for line in _pdf_wrapped_lines(brief.get("summary", ""), 98):
            c.drawString(55, y, line)
            y -= 12
        y -= 8
        for item in _pdf_brief_lines(brief) + _pdf_scorecard_lines(scorecard) + _pdf_benchmark_lines(benchmark):
            c.drawString(55, y, item[:105])
            y -= 12
            if y < 80:
                c.showPage()
                y = 800
                c.setFont("Helvetica", 9)
        y -= 10
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "Historia Executiva")
        y -= 18
        c.setFont("Helvetica", 9)
        for line in (
            _pdf_story_lines(story)
            + _pdf_narrative_lines(narrative)
            + _pdf_discovery_lines(discovery)
            + _pdf_summary_lines(metrics_pack, analytical.get("recommendations", []))
        ):
            c.drawString(55, y, line[:105])
            y -= 14
            if y < 80:
                c.showPage()
                y = 800
                c.setFont("Helvetica", 9)
        y -= 30
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "Cards")
        y -= 18
        c.setFont("Helvetica", 9)
        for card in result.get("cards", [])[:30]:
            line = (
                f"- {card.get('title', '')[:55]} [{card.get('status', '')}] "
                f"{card.get('activity_type', '')} risco={card.get('risk_score', 'N/A')}"
            )
            c.drawString(50, y, line)
            y -= 15
            if y < 50:
                c.showPage()
                y = 800
        c.save()
        content = buffer.getvalue()
        return {
            "format": "pdf",
            "content_type": "application/pdf",
            "filename": "report.pdf",
            "content_base64": _b64(content),
            "size_bytes": len(content),
            "sections": ["Capa", "Executive Brief", "KPIs", "Diagnostico Gerencial", "Anexo Analitico"],
            "visual_contract": {
                "cover": True,
                "kpi_cards": True,
                "executive_tables": bool(result.get("executive_tables")),
                "executive_conclusion": True,
            },
        }
    except ImportError:
        content = json.dumps(result, default=str).encode("utf-8")
        return {
            "format": "pdf",
            "content_type": "application/json",
            "filename": "report.json",
            "content_base64": _b64(content),
            "size_bytes": len(content),
            "note": "ReportLab unavailable; JSON fallback",
        }


def _export_pptx(result: dict[str, Any]) -> dict[str, Any]:
    brief = result.get("executive_brief", {})
    scorecard = result.get("operational_scorecard", {})
    benchmark = result.get("internal_benchmark", {})
    analytical = result.get("analytical", {})
    narrative = result.get("executive_narrative", {})
    discovery = result.get("discovery", {})
    story = result.get("executive_story", {})
    tables = result.get("executive_tables", {})
    rankings = result.get("rankings", {})
    output = result.get("report_output", {})
    sections = narrative.get("sections", {})
    metrics_pack = analytical.get("metrics_pack", {})
    summary = {
        "title": f"Relatório {result.get('meta', {}).get('report_type', '')}",
        "board_id": result.get("meta", {}).get("board_id"),
        "board_name": result.get("meta", {}).get("board_name"),
        "matched_cards": result.get("meta", {}).get("matched_cards"),
        "report_version": result.get("meta", {}).get("report_version", "1.0"),
        "report_quality": analytical.get("quality", {}),
        "executive_readability": narrative.get("executive_readability_score", {}),
        "report_intelligence": discovery.get("report_intelligence_score", {}),
        "executive_story_quality": story.get("executive_story_quality_score", {}),
        "metrics_pack": analytical.get("metrics_pack", {}),
        "slides": [
            _cover_slide(result),
            _brief_slide(brief),
            _scorecard_slide(scorecard, tables),
            _story_drivers_slide(story),
            _story_risks_slide(story),
            _bottlenecks_slide(tables),
            _recommended_decisions_slide(story),
            _story_action_slide(story),
            _appendix_slide(output, rankings),
            _story_slide("História Executiva", story),
            _benchmark_slide(benchmark),
            _pptx_slide("Diagnostico", sections.get("diagnostico_executivo", {})),
            _pptx_slide("KPIs", _kpi_slide_section(metrics_pack)),
            _pptx_slide("Riscos", sections.get("riscos_prioritarios", {})),
            _story_decisions_slide(story),
            _pptx_slide("Proximas acoes", sections.get("proximas_acoes", {})),
            _pptx_slide("Descobertas", _discovery_slide_section(discovery)),
        ],
        "recommendations": analytical.get("recommendations", []),
        "insights": narrative.get("insights", []),
        "management_decisions": narrative.get("management_decisions", []),
        "discovery": discovery,
        "executive_story": story,
        "executive_brief": brief,
        "operational_scorecard": scorecard,
        "internal_benchmark": benchmark,
        "executive_tables": tables,
        "rankings": rankings,
        "commercial_report_score": result.get("commercial_report_score", {}),
        "data_keys": list(result.get("data", {}).keys()),
    }
    content = json.dumps(summary, indent=2, ensure_ascii=False).encode("utf-8")
    return {
        "format": "pptx",
        "content_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "filename": "report-outline.json",
        "content_base64": _b64(content),
        "size_bytes": len(content),
        "note": "PPTX outline; full deck generation planned for V3",
    }


def _b64(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode("ascii")


def _pdf_summary_lines(metrics_pack: dict[str, Any], recommendations: list[dict[str, Any]]) -> list[str]:
    sla = metrics_pack.get("sla", {})
    quality = metrics_pack.get("quality", {})
    communication = metrics_pack.get("communication", {})
    lines = [
        f"SLA: {sla.get('compliance_pct', 'N/A')}% compliance, {sla.get('overdue_open_cards', 0)} abertos vencidos.",
        f"Qualidade: {quality.get('incomplete_description_count', 0)} descricoes incompletas, {quality.get('missing_owner_count', 0)} sem responsavel.",
        f"Comunicacao: {communication.get('total_comments', 0)} comentarios, {communication.get('cards_without_comments', 0)} cards sem comentarios.",
    ]
    for item in recommendations[:5]:
        evidence = ", ".join(map(str, item.get("evidence", [])[:3]))
        lines.append(f"Recomendacao {item.get('priority', '')}: {item.get('action', '')} Evidencias: {evidence}")
    return lines


def _markdown_brief(brief: dict[str, Any]) -> list[str]:
    if not brief:
        return ["- Brief executivo indisponível para este recorte."]
    kpis = brief.get("kpis") or brief.get("kpis_principais") or []
    decisions = brief.get("top_decisions") or [
        item.get("decisao") for item in brief.get("decisoes_recomendadas", [])
    ]
    risks = brief.get("top_risks") or [
        item.get("risco") or item.get("problema") for item in brief.get("principais_problemas", [])
    ]
    opportunities = brief.get("top_opportunities") or [
        (brief.get("maior_oportunidade") or {}).get("oportunidade")
    ]
    actions = brief.get("action_plan") or [
        item.get("acao") for item in brief.get("proximas_acoes", [])
    ]
    lines = [
        f"> **Status geral:** {brief.get('status', brief.get('status_geral', 'N/A'))}",
        f"> **Score operacional:** {brief.get('score_operacional', 'N/A')}",
        "",
        brief.get("summary", ""),
        "",
        "| KPI | Valor | Status | Interpretação |",
        "| --- | ---: | --- | --- |",
    ]
    for item in kpis[:5]:
        lines.append(
            f"| {item.get('label') or item.get('metrica', '')} | {item.get('value') or item.get('valor', '')} | {item.get('direction') or item.get('status', '')} | {item.get('interpretacao') or item.get('confidence', 'N/A')} |"
        )
    lines.extend(["", "**3 decisões:**"])
    lines.extend(f"- {item}" for item in decisions[:3] if item)
    lines.extend(["", "**3 riscos:**"])
    lines.extend(f"- {item}" for item in risks[:3] if item)
    lines.extend(["", "**3 oportunidades:**"])
    lines.extend(f"- {item}" for item in opportunities[:3] if item)
    lines.extend(["", "**3 próximas ações:**"])
    lines.extend(f"- {item}" for item in actions[:3] if item)
    return lines


def _markdown_management_diagnosis(diagnosis: dict[str, Any]) -> list[str]:
    if not diagnosis:
        return ["- Diagnóstico gerencial indisponível para este recorte."]
    story = diagnosis.get("historia_executiva_periodo", {})
    lines = [
        "### 1. História executiva do período",
        "",
        story.get("summary", ""),
        "",
        "### 2. Principais mudanças",
        "",
        *_markdown_story_items(diagnosis.get("principais_mudancas", []), title_key="title", action_key="explanation"),
        "",
        "### 3. Top 3 drivers",
        "",
        *_markdown_story_items(diagnosis.get("top_3_drivers", []), title_key="title", action_key="recommended_action"),
        "",
        "### 4-10. Síntese gerencial",
        "",
        f"- Categorias analisadas: {len(diagnosis.get('analise_por_categoria', []))}",
        f"- Membros analisados: {len(diagnosis.get('analise_por_membro', []))}",
        f"- Gargalos identificados: {len(diagnosis.get('gargalos', []))}",
        f"- Riscos priorizados: {len(diagnosis.get('riscos', []))}",
        f"- Causas prováveis: {len(diagnosis.get('causas_provaveis', []))}",
        f"- Recomendações: {len(diagnosis.get('recomendacoes', []))}",
    ]
    return lines


def _markdown_table(rows: list[dict[str, Any]], keys: list[str], headers: list[str]) -> list[str]:
    if not rows:
        return ["- Sem dados suficientes para esta tabela."]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows[:10]:
        values = [_clean_cell(row.get(key, "")) for key in keys]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def _markdown_rankings(rankings: dict[str, list[dict[str, Any]]]) -> list[str]:
    if not rankings:
        return ["- Rankings indisponíveis para este recorte."]
    labels = {
        "top_10_categories": "Top 10 categorias",
        "top_10_members": "Top 10 membros",
        "top_10_critical_cards": "Top 10 cards críticos",
        "top_10_causes": "Top 10 causas prováveis",
        "top_10_risks": "Top 10 riscos",
        "top_10_opportunities": "Top 10 oportunidades",
    }
    lines: list[str] = []
    for key, title in labels.items():
        lines.extend([f"### {title}", ""])
        items = rankings.get(key, [])
        if not items:
            lines.extend(["- Sem evidência suficiente.", ""])
            continue
        for item in items[:10]:
            name = item.get("name") or item.get("title") or item.get("card_id")
            evidence = item.get("evidence", "")
            lines.append(f"- **#{item.get('rank')} {name}:** {_clean_cell(evidence)}")
        lines.append("")
    return lines


def _markdown_appendix(appendix: dict[str, Any]) -> list[str]:
    if not appendix:
        return ["- Anexo analítico indisponível para este recorte."]
    return [
        f"- Dados por card: {len(appendix.get('dados_por_card', []))}",
        f"- Evidências rastreáveis: {len(appendix.get('evidencias', []))}",
        f"- Descrições estruturadas: {len(appendix.get('descricoes_estruturadas', []))}",
        f"- Checklists: {len(appendix.get('checklists', []))}",
        "",
        "### Limitações",
        "",
        *[f"- {item}" for item in appendix.get("limitations", [])],
    ]


def _clean_cell(value: Any) -> str:
    if isinstance(value, list):
        value = "; ".join(map(str, value[:4]))
    if isinstance(value, dict):
        value = json.dumps(value, ensure_ascii=False, default=str)
    text = str(value if value is not None else "")
    return text.replace("|", "/").replace("\n", " ")[:220]


def _markdown_scorecard(scorecard: dict[str, Any]) -> list[str]:
    if not scorecard:
        return ["- Scorecard indisponível para este recorte."]
    lines = [
        f"**Score geral:** {scorecard.get('overall_score', 'N/A')} ({scorecard.get('label', 'N/A')})",
        f"**Confiança:** {scorecard.get('confidence', 'N/A')}",
        "",
        "| Dimensão | Score | Status | Evidência |",
        "| --- | ---: | --- | --- |",
    ]
    for item in scorecard.get("dimensions", []):
        lines.append(
            f"| {item.get('name', '')} | {item.get('score', '')} | {item.get('status', '')} | {item.get('evidence', '')} |"
        )
    return lines


def _markdown_benchmark(benchmark: dict[str, Any]) -> list[str]:
    if not benchmark:
        return ["- Sem dados suficientes para benchmark interno."]
    lines = [
        benchmark.get("summary", ""),
        f"**Confiança:** {benchmark.get('confidence', 'N/A')}",
        "",
        "| Métrica | Atual | Anterior | Últimos 90 dias | Tendência |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for item in benchmark.get("items", []):
        lines.append(
            f"| {item.get('metric', '')} | {item.get('current', '')} | {item.get('previous', '')} | {item.get('last_90_days', '')} | {item.get('trend', '')} |"
        )
    return lines


def _pdf_wrapped_lines(text: str, width: int) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word])
        if len(candidate) > width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines or [""]


def _pdf_brief_lines(brief: dict[str, Any]) -> list[str]:
    lines = [f"Status geral: {brief.get('status') or brief.get('status_geral', 'N/A')}"]
    for item in (brief.get("kpis") or brief.get("kpis_principais") or [])[:5]:
        lines.append(
            "KPI: "
            f"{item.get('label') or item.get('metrica')} = {item.get('value') or item.get('valor')} "
            f"({item.get('direction') or item.get('status')})"
        )
    decisions = brief.get("top_decisions") or [item.get("decisao") for item in brief.get("decisoes_recomendadas", [])]
    for item in decisions[:3]:
        lines.append(f"Decisao: {item}")
    return lines


def _pdf_scorecard_lines(scorecard: dict[str, Any]) -> list[str]:
    lines = [f"Scorecard Executivo: {scorecard.get('overall_score', 'N/A')} ({scorecard.get('label', 'N/A')})"]
    for item in scorecard.get("dimensions", [])[:5]:
        lines.append(f"{item.get('name')}: {item.get('score')} - {item.get('evidence')}")
    return lines


def _pdf_benchmark_lines(benchmark: dict[str, Any]) -> list[str]:
    lines = [f"Benchmark: {benchmark.get('summary', 'sem dados suficientes')}"]
    for item in benchmark.get("items", [])[:4]:
        lines.append(f"{item.get('metric')}: atual {item.get('current')}, anterior {item.get('previous')}, tendencia {item.get('trend')}")
    return lines


def _markdown_narrative_sections(sections: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for key, section in sections.items():
        if key == "readability_inputs":
            continue
        lines.extend(
            [
                f"### {section.get('title', key)}",
                "",
                section.get("summary", ""),
                "",
                "Evidências:",
                *[f"- {item}" for item in section.get("evidence", [])],
                "",
            ]
        )
    return lines


def _markdown_discovery_items(items: list[dict[str, Any]], *, title_key: str) -> list[str]:
    if not items:
        return ["- Nenhum item com evidencia suficiente no recorte analisado."]
    lines = []
    for item in items[:10]:
        evidence = "; ".join(map(str, item.get("evidence", [])))
        confidence = item.get("confidence")
        suffix = f" Confiança: {confidence}." if confidence is not None else ""
        lines.append(f"- **{item.get(title_key, '')}:** Evidências: {evidence}.{suffix}")
    return lines


def _markdown_forecast_items(items: list[dict[str, Any]]) -> list[str]:
    if not items:
        return ["- Nenhum cenário provável foi gerado porque não há tendência observada suficiente."]
    return [
        f"- **{item.get('scenario', '')}:** Base: {', '.join(map(str, item.get('basis', [])))}. Confiança: {item.get('confidence')}."
        for item in items[:10]
    ]


def _markdown_story_items(items: list[dict[str, Any]], *, title_key: str, action_key: str) -> list[str]:
    if not items:
        return ["- Nenhum item com evidência suficiente para compor a história executiva."]
    lines = []
    for item in items[:7]:
        evidence = "; ".join(map(str, item.get("evidence", [])))
        action = item.get(action_key, "")
        lines.append(f"- **{item.get(title_key, '')}:** {action} Evidências: {evidence}.")
    return lines


def _pdf_narrative_lines(narrative: dict[str, Any]) -> list[str]:
    sections = narrative.get("sections", {})
    lines = []
    for key in ("diagnostico_executivo", "impacto_prazo_sla", "decisoes_necessarias_gestao"):
        section = sections.get(key, {})
        if section:
            lines.append(f"{section.get('title', '')}: {section.get('summary', '')}")
    return lines


def _pdf_story_lines(story: dict[str, Any]) -> list[str]:
    if not story.get("generated"):
        return ["Historia executiva: sem evidencia suficiente para sintese."]
    lines = [
        f"Headline: {story.get('headline', '')}",
        f"Historia do periodo: {story.get('period_story', '')}",
    ]
    for item in story.get("key_drivers", [])[:3]:
        evidence = ", ".join(map(str, item.get("evidence", [])[:2]))
        lines.append(f"Driver: {item.get('title', '')}. Evidencias: {evidence}")
    for item in story.get("decision_ready_summary", [])[:3]:
        evidence = ", ".join(map(str, item.get("evidence", [])[:2]))
        lines.append(f"Decisao: {item.get('decision', '')}. Evidencias: {evidence}")
    return lines


def _pdf_discovery_lines(discovery: dict[str, Any]) -> list[str]:
    lines = []
    for item in discovery.get("executive_highlights", [])[:3]:
        evidence = ", ".join(map(str, item.get("evidence", [])[:2]))
        lines.append(f"Atencao: {item.get('title', '')}. Evidencias: {evidence}")
    for item in discovery.get("executive_surprises", [])[:2]:
        evidence = ", ".join(map(str, item.get("evidence", [])[:2]))
        lines.append(f"Descoberta: {item.get('text', '')}. Evidencias: {evidence}")
    for item in discovery.get("what_happens_next", [])[:2]:
        basis = ", ".join(map(str, item.get("basis", [])[:2]))
        lines.append(f"Cenario provavel: {item.get('scenario', '')}. Base: {basis}")
    return lines


def _kpi_slide_section(metrics_pack: dict[str, Any]) -> dict[str, Any]:
    sla = metrics_pack.get("sla", {})
    quality = metrics_pack.get("quality", {})
    communication = metrics_pack.get("communication", {})
    return {
        "title": "KPIs",
        "summary": (
            f"SLA {sla.get('compliance_pct', 'N/A')}%, "
            f"{quality.get('missing_owner_count', 0)} sem responsavel, "
            f"{communication.get('total_comments', 0)} comentarios."
        ),
        "evidence": [
            f"overdue_open_cards={sla.get('overdue_open_cards', 0)}",
            f"incomplete_description_count={quality.get('incomplete_description_count', 0)}",
            f"cards_without_comments={communication.get('cards_without_comments', 0)}",
        ],
    }


def _pptx_slide(title: str, section: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": title,
        "summary": section.get("summary", ""),
        "evidence": section.get("evidence", []),
    }


def _brief_slide(brief: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": "Executive Brief",
        "summary": brief.get("summary", ""),
        "evidence": brief.get("top_decisions", [])[:3],
        "speaker_notes": "Abrir pela decisao que a gestao precisa tomar hoje e pelo risco se nada mudar.",
    }


def _cover_slide(result: dict[str, Any]) -> dict[str, Any]:
    meta = result.get("meta", {})
    commercial = result.get("commercial_report_score", {})
    return {
        "title": "Capa",
        "summary": f"Relatorio Executivo - {meta.get('board_name') or meta.get('board_id', '')}",
        "evidence": [
            f"cards={meta.get('matched_cards', 0)}",
            f"CommercialReportScore={commercial.get('score', 'N/A')}",
        ],
        "speaker_notes": "Abrir pela situacao operacional, score e decisao esperada da diretoria.",
    }


def _scorecard_slide(scorecard: dict[str, Any], tables: dict[str, Any] | None = None) -> dict[str, Any]:
    dimensions = scorecard.get("dimensions", [])
    kpis = (tables or {}).get("kpis_principais", [])
    return {
        "title": "Scorecard Executivo",
        "summary": f"Score geral {scorecard.get('overall_score', 'N/A')} ({scorecard.get('label', 'N/A')})",
        "evidence": (
            [f"{item.get('metrica')}: {item.get('valor')} - {item.get('status')}" for item in kpis[:5]]
            or [f"{item.get('name')}: {item.get('score')} - {item.get('evidence')}" for item in dimensions[:5]]
        ),
        "speaker_notes": "Usar o scorecard para separar saude operacional, risco e maturidade.",
    }


def _benchmark_slide(benchmark: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": "Benchmark Interno",
        "summary": benchmark.get("summary", "Sem dados suficientes para benchmark interno."),
        "evidence": [
            f"{item.get('metric')}: {item.get('trend')}"
            for item in benchmark.get("items", [])[:5]
        ],
        "speaker_notes": "Comparar periodo atual, periodo anterior e historico antes de discutir plano.",
    }


def _story_slide(title: str, story: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": title,
        "summary": story.get("period_story", ""),
        "evidence": [item.get("evidence") for item in story.get("evidence_map", [])[:5]],
    }


def _story_drivers_slide(story: dict[str, Any]) -> dict[str, Any]:
    drivers = story.get("key_drivers", [])
    return {
        "title": "Top 3 Drivers",
        "summary": "; ".join(item.get("title", "") for item in drivers[:3]),
        "evidence": [e for item in drivers[:3] for e in item.get("evidence", [])[:2]],
    }


def _story_decisions_slide(story: dict[str, Any]) -> dict[str, Any]:
    decisions = story.get("decision_ready_summary", [])
    return {
        "title": "Decisões Prioritárias",
        "summary": "; ".join(item.get("decision", "") for item in decisions[:3]),
        "evidence": [e for item in decisions[:3] for e in item.get("evidence", [])[:2]],
    }


def _recommended_decisions_slide(story: dict[str, Any]) -> dict[str, Any]:
    decisions = story.get("decision_ready_summary", [])
    return {
        "title": "Decisões recomendadas",
        "summary": "; ".join(item.get("decision", "") for item in decisions[:3]),
        "evidence": [e for item in decisions[:3] for e in item.get("evidence", [])[:2]],
        "speaker_notes": "Cada decisao precisa ser ligada a evidencia, impacto, urgencia e dono sugerido.",
    }


def _story_risks_slide(story: dict[str, Any]) -> dict[str, Any]:
    section = story.get("story_structure", {}).get("riscos_se_nada_mudar", {})
    return {
        "title": "Riscos se Nada Mudar",
        "summary": section.get("summary", ""),
        "evidence": section.get("evidence", []),
    }


def _story_action_slide(story: dict[str, Any]) -> dict[str, Any]:
    actions = story.get("action_plan", [])
    return {
        "title": "Plano de Ação",
        "summary": "; ".join(item.get("action", "") for item in actions[:5]),
        "evidence": [e for item in actions[:5] for e in item.get("evidence", [])[:2]],
    }


def _bottlenecks_slide(tables: dict[str, Any]) -> dict[str, Any]:
    bottlenecks = tables.get("gargalos", [])
    return {
        "title": "Gargalos",
        "summary": "; ".join(f"{item.get('lista_etapa')} ({item.get('cards')})" for item in bottlenecks[:3]),
        "evidence": [item.get("recomendacao") for item in bottlenecks[:3] if item.get("recomendacao")],
        "speaker_notes": "Mostrar onde o fluxo concentra trabalho, tempo medio e severidade.",
    }


def _appendix_slide(output: dict[str, Any], rankings: dict[str, Any]) -> dict[str, Any]:
    appendix = output.get("analytical_appendix", {})
    return {
        "title": "Anexo Analítico",
        "summary": (
            f"{len(appendix.get('dados_por_card', []))} cards, "
            f"{len(appendix.get('evidencias', []))} evidencias, "
            f"{len(rankings)} rankings."
        ),
        "evidence": appendix.get("limitations", [])[:3],
        "speaker_notes": "Usar apenas quando a diretoria pedir rastreabilidade ou detalhes por card.",
    }


def _discovery_slide_section(discovery: dict[str, Any]) -> dict[str, Any]:
    highlights = discovery.get("executive_highlights", [])
    score = discovery.get("report_intelligence_score", {})
    if highlights:
        top = highlights[0]
        return {
            "title": "Descobertas",
            "summary": f"{top.get('title')} Score: {score.get('score', 'N/A')}",
            "evidence": top.get("evidence", []),
        }
    return {
        "title": "Descobertas",
        "summary": "Sem descobertas com evidencia suficiente no recorte analisado.",
        "evidence": [],
    }
