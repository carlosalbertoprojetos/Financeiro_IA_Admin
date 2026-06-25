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
    writer.writerow(["card_id", "title", "status"])
    for card in result.get("cards", []):
        writer.writerow([card.get("id"), card.get("title"), card.get("status")])
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
    lines = [
        f"# Relatório {meta.get('report_type', '')}",
        "",
        f"**Board:** {meta.get('board_id', '')}",
        f"**Cards:** {meta.get('matched_cards', 0)}",
        "",
        "## Resumo",
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

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        y = 800
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, f"Relatório {result.get('meta', {}).get('report_type', '')}")
        y -= 30
        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Board: {result.get('meta', {}).get('board_id', '')}")
        y -= 20
        c.drawString(50, y, f"Cards: {result.get('meta', {}).get('matched_cards', 0)}")
        y -= 30
        for card in result.get("cards", [])[:30]:
            line = f"- {card.get('title', '')[:80]} [{card.get('status', '')}]"
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
    summary = {
        "title": f"Relatório {result.get('meta', {}).get('report_type', '')}",
        "board_id": result.get("meta", {}).get("board_id"),
        "matched_cards": result.get("meta", {}).get("matched_cards"),
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
