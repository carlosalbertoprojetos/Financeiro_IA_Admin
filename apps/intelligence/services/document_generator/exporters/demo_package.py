from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from apps.intelligence.services.document_generator.builders import (
    build_executive_docx,
    build_executive_pdf,
    build_executive_pptx,
    build_executive_xlsx,
)
from apps.intelligence.services.document_generator.charts.factory import build_chart_specs
from apps.intelligence.services.document_generator.presentation import BrandingConfig, PresentationModel
from apps.intelligence.services.document_generator.templates.themes import get_theme
from apps.intelligence.services.document_generator.validators import (
    validate_docx,
    validate_pdf,
    validate_pptx,
    validate_xlsx,
)


def build_demo_package(
    output_contract: dict[str, Any],
    *,
    output_dir: str | Path = "docs/demo_package",
    theme: str = "corporate",
    branding: BrandingConfig | None = None,
) -> dict[str, Any]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    model = PresentationModel.from_output_contract(
        output_contract,
        branding=branding,
        theme=get_theme(theme),
    )
    model = model.with_charts(build_chart_specs(output_contract))

    artifacts = {
        "executive_report.pdf": build_executive_pdf(model),
        "executive_report.pptx": build_executive_pptx(model),
        "executive_report.xlsx": build_executive_xlsx(model),
        "executive_report.docx": build_executive_docx(model),
        "executive_report.json": json.dumps(output_contract, indent=2, ensure_ascii=False, default=str).encode("utf-8"),
        "executive_report.md": _markdown(model).encode("utf-8"),
    }
    for filename, content in artifacts.items():
        (directory / filename).write_bytes(content)

    validation = {
        "pdf": validate_pdf(artifacts["executive_report.pdf"], expected_sections=set(model.sections)),
        "pptx": validate_pptx(artifacts["executive_report.pptx"]),
        "xlsx": validate_xlsx(artifacts["executive_report.xlsx"]),
        "docx": validate_docx(artifacts["executive_report.docx"]),
    }
    (directory / "validation.json").write_text(
        json.dumps(validation, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return {
        "output_dir": str(directory),
        "artifacts": sorted(artifacts),
        "validation": validation,
        "status": "PASS" if all(item["status"] == "PASS" for item in validation.values()) else "FAIL",
    }


def _markdown(model: PresentationModel) -> str:
    lines = [
        f"# {model.title}",
        "",
        "## Executive Brief",
        "",
        model.executive_brief.get("summary", ""),
        "",
        "## KPIs",
        "",
        "| Metrica | Valor | Status |",
        "| --- | ---: | --- |",
    ]
    for item in model.kpis:
        lines.append(f"| {item.get('metrica')} | {item.get('valor')} | {item.get('status')} |")
    lines.extend(["", "## Decisoes", ""])
    for item in model.decisions:
        lines.append(f"- {item.get('decisao')} Evidencia: {item.get('evidencia')}")
    lines.extend(["", "## Evidencias", ""])
    for item in model.evidence[:20]:
        lines.append(f"- {item.get('claim')}: {item.get('evidence')}")
    return "\n".join(lines)
