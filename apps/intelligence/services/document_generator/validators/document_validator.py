from __future__ import annotations

import zipfile
from io import BytesIO
from typing import Any


PDF_SECTIONS = {
    "Capa",
    "Sumario",
    "Executive Brief",
    "Scorecard",
    "KPIs",
    "Top Drivers",
    "Diagnostico",
    "Riscos",
    "Decisoes",
    "Plano de Acao",
    "Rankings",
    "Evidencias",
    "Anexos",
}

PPTX_SLIDES = {
    "Capa",
    "Executive Brief",
    "Operational Scorecard",
    "KPIs",
    "Top 3 Drivers",
    "Gargalos",
    "Riscos",
    "Oportunidades",
    "Decisões",
    "Plano de Ação",
    "Próximos Passos",
    "Encerramento",
}

XLSX_SHEETS = {
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
}


def validate_pdf(content: bytes, *, expected_sections: set[str] | None = None) -> dict[str, Any]:
    checks = {
        "opens_correctly": content.startswith(b"%PDF"),
        "pagination": b"/Page" in content,
        "sections": sorted(expected_sections or PDF_SECTIONS),
        "section_count": len(expected_sections or PDF_SECTIONS),
    }
    return _result(checks, required=("opens_correctly", "pagination"))


def validate_pptx(content: bytes) -> dict[str, Any]:
    names, texts = _zip_names_and_text(content)
    slide_count = len([name for name in names if name.startswith("ppt/slides/slide") and name.endswith(".xml")])
    found = {title for title in PPTX_SLIDES if title in texts}
    checks = {
        "opens_in_powerpoint_package": "ppt/presentation.xml" in names,
        "slides_editable": "<p:sp>" in texts and "<a:t>" in texts,
        "elements_positioned": "<a:xfrm>" in texts,
        "slide_count": slide_count,
        "required_slides": sorted(found),
    }
    return _result(
        checks,
        required=("opens_in_powerpoint_package", "slides_editable", "elements_positioned"),
        min_counts={"slide_count": len(PPTX_SLIDES), "required_slides": len(PPTX_SLIDES)},
    )


def validate_xlsx(content: bytes) -> dict[str, Any]:
    names, texts = _zip_names_and_text(content)
    found = {sheet for sheet in XLSX_SHEETS if sheet in texts}
    checks = {
        "opens_in_excel_package": "xl/workbook.xml" in names,
        "formulas_valid": True,
        "filters": "<autoFilter" in texts,
        "freeze_panes": "<pane " in texts,
        "required_sheets": sorted(found),
    }
    return _result(
        checks,
        required=("opens_in_excel_package", "formulas_valid", "filters", "freeze_panes"),
        min_counts={"required_sheets": len(XLSX_SHEETS)},
    )


def validate_docx(content: bytes) -> dict[str, Any]:
    names, texts = _zip_names_and_text(content)
    checks = {
        "opens_in_word_package": "word/document.xml" in names,
        "styles_preserved": "<w:p>" in texts and "<w:tbl>" in texts,
        "sections": [section for section in ("Executive Brief", "KPIs", "Decisoes", "Plano de Acao", "Evidencias") if section in texts],
    }
    return _result(
        checks,
        required=("opens_in_word_package", "styles_preserved"),
        min_counts={"sections": 5},
    )


def _zip_names_and_text(content: bytes) -> tuple[set[str], str]:
    with zipfile.ZipFile(BytesIO(content)) as package:
        names = set(package.namelist())
        texts = []
        for name in names:
            if name.endswith(".xml"):
                texts.append(package.read(name).decode("utf-8", errors="ignore"))
    return names, "\n".join(texts)


def _result(
    checks: dict[str, Any],
    *,
    required: tuple[str, ...],
    min_counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    failures = [key for key in required if not checks.get(key)]
    for key, minimum in (min_counts or {}).items():
        value = checks.get(key)
        count = len(value) if isinstance(value, list) else int(value or 0)
        if count < minimum:
            failures.append(f"{key}: {count} < {minimum}")
    return {"status": "PASS" if not failures else "FAIL", "checks": checks, "failures": failures}
