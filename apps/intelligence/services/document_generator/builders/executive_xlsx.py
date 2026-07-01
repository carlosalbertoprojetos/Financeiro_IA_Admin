from __future__ import annotations

from apps.intelligence.services.document_generator.builders.ooxml import xml_escape, zip_bytes
from apps.intelligence.services.document_generator.presentation import PresentationModel


SHEETS = [
    "Executive Brief",
    "KPIs",
    "Categorias",
    "Membros",
    "SLA",
    "Timeline",
    "Cards",
    "Comentarios",
    "Checklists",
    "Evidencias",
    "Base Completa",
]


def build_executive_xlsx(model: PresentationModel) -> bytes:
    sheet_payloads = _sheet_payloads(model)
    files = {
        "[Content_Types].xml": _content_types(len(SHEETS)),
        "_rels/.rels": _root_rels(),
        "xl/workbook.xml": _workbook(),
        "xl/_rels/workbook.xml.rels": _workbook_rels(len(SHEETS)),
        "xl/styles.xml": _styles(),
    }
    for index, name in enumerate(SHEETS, start=1):
        files[f"xl/worksheets/sheet{index}.xml"] = _sheet(sheet_payloads.get(name, []))
    return zip_bytes(files)


def _sheet_payloads(model: PresentationModel) -> dict[str, list[list[object]]]:
    appendix = model.appendix
    return {
        "Executive Brief": [["Status", model.executive_brief.get("status_geral")], ["Score", model.executive_brief.get("score_operacional")], ["Resumo", model.executive_brief.get("summary")]],
        "KPIs": [["Metrica", "Valor", "Status", "Interpretacao"], *[[i.get("metrica"), i.get("valor"), i.get("status"), i.get("interpretacao")] for i in model.kpis]],
        "Categorias": _rows_from_dicts(model.tables.get("top_categorias", [])),
        "Membros": _rows_from_dicts(model.tables.get("top_membros", [])),
        "SLA": _rows_from_dicts(model.tables.get("kpis_principais", [])),
        "Timeline": _rows_from_dicts((model.timeline or {}).get("created_by_month", [])) if isinstance(model.timeline, dict) else [],
        "Cards": _rows_from_dicts(appendix.get("dados_por_card", [])),
        "Comentarios": _rows_from_dicts([appendix.get("comentarios_relevantes", {})]),
        "Checklists": _rows_from_dicts(appendix.get("checklists", [])),
        "Evidencias": _rows_from_dicts(model.evidence),
        "Base Completa": _rows_from_dicts(appendix.get("dados_por_card", [])),
    }


def _rows_from_dicts(rows: list[dict]) -> list[list[object]]:
    if not rows:
        return [["Sem dados"]]
    keys = list(rows[0].keys())
    return [keys, *[[row.get(key, "") for key in keys] for row in rows[:200]]]


def _sheet(rows: list[list[object]]) -> str:
    xml_rows = []
    for row_index, row in enumerate(rows or [["Sem dados"]], start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            ref = f"{_col(col_index)}{row_index}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{xml_escape(value)}</t></is></c>')
        xml_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    last_col = _col(max(len(row) for row in rows) if rows else 1)
    last_row = max(len(rows), 1)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
        f'<sheetData>{"".join(xml_rows)}</sheetData>'
        f'<autoFilter ref="A1:{last_col}{last_row}"/>'
        "</worksheet>"
    )


def _workbook() -> str:
    sheets = "".join(f'<sheet name="{xml_escape(name)}" sheetId="{index}" r:id="rId{index}"/>' for index, name in enumerate(SHEETS, start=1))
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{sheets}</sheets></workbook>"
    )


def _workbook_rels(count: int) -> str:
    rels = "".join(
        f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
        for index in range(1, count + 1)
    )
    rels += f'<Relationship Id="rId{count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    return f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rels}</Relationships>'


def _root_rels() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )


def _content_types(count: int) -> str:
    sheets = "".join(
        f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for index in range(1, count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        f"{sheets}</Types>"
    )


def _styles() -> str:
    return '<?xml version="1.0" encoding="UTF-8"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="1"><font><sz val="11"/></font></fonts><fills count="1"><fill><patternFill patternType="none"/></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs><cellXfs count="1"><xf/></cellXfs></styleSheet>'


def _col(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result
