from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_BASELINE_FILE = "docs/report_quality_baseline.json"
REQUIRED_SECTIONS = (
    "contexto_periodo",
    "principais_mudancas",
    "fatores_resultado",
    "causas_provaveis",
    "impactos_operacionais",
    "riscos_se_nada_mudar",
    "oportunidades",
    "decisoes_prioritarias",
    "plano_acao",
)
REQUIRED_EXPORTS = ("json", "markdown", "pdf", "pptx")


def build_baseline(validation: dict[str, Any], *, eor_model: str = "1.1") -> dict[str, Any]:
    return {
        "baseline_date": date.today().isoformat(),
        "eor_model": eor_model,
        "minimum_scores": {
            "DecisionValueScore": int(validation.get("decision_value_score") or 0),
            "ReportQualityScore": _latest_stage_score(validation, "report_quality_score"),
            "ReportIntelligenceScore": _latest_stage_score(validation, "report_intelligence_score"),
            "ExecutiveStoryQualityScore": _latest_stage_score(validation, "executive_story_quality_score"),
        },
        "required_sections": list(REQUIRED_SECTIONS),
        "required_exports": list(REQUIRED_EXPORTS),
        "required_checks": [
            key for key, value in (validation.get("checks") or {}).items() if value is True
        ],
    }


def save_baseline(validation: dict[str, Any], baseline_file: str, *, eor_model: str = "1.1") -> dict[str, Any]:
    path = Path(baseline_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    baseline = build_baseline(validation, eor_model=eor_model)
    path.write_text(json.dumps(baseline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return baseline


def load_baseline(baseline_file: str) -> dict[str, Any]:
    path = Path(baseline_file)
    if not path.exists():
        raise FileNotFoundError(f"Baseline file not found: {baseline_file}")
    return json.loads(path.read_text(encoding="utf-8"))


def compare_to_baseline(
    validation: dict[str, Any],
    baseline: dict[str, Any],
    *,
    tolerance: int = 0,
) -> dict[str, Any]:
    current_scores = {
        "DecisionValueScore": int(validation.get("decision_value_score") or 0),
        "ReportQualityScore": _latest_stage_score(validation, "report_quality_score"),
        "ReportIntelligenceScore": _latest_stage_score(validation, "report_intelligence_score"),
        "ExecutiveStoryQualityScore": _latest_stage_score(validation, "executive_story_quality_score"),
    }
    minimum_scores = baseline.get("minimum_scores") or {}
    score_diffs = []
    regressions = []
    for name, minimum in minimum_scores.items():
        current = int(current_scores.get(name) or 0)
        required = int(minimum or 0) - int(tolerance or 0)
        diff = current - int(minimum or 0)
        item = {
            "metric": name,
            "current": current,
            "baseline": int(minimum or 0),
            "difference": diff,
            "tolerance": int(tolerance or 0),
            "required_with_tolerance": required,
            "passed": current >= required,
        }
        score_diffs.append(item)
        if not item["passed"]:
            regressions.append(
                f"{name} regressed: current={current}, baseline={minimum}, tolerance={tolerance}"
            )

    missing_sections = _missing_required_sections(validation, baseline.get("required_sections") or [])
    missing_exports = _missing_required_exports(validation, baseline.get("required_exports") or [])
    missing_checks = [
        key for key in baseline.get("required_checks", []) if not (validation.get("checks") or {}).get(key)
    ]
    for key in missing_sections:
        regressions.append(f"required section missing: {key}")
    for key in missing_exports:
        regressions.append(f"required export missing: {key}")
    for key in missing_checks:
        regressions.append(f"required check failed: {key}")

    return {
        "status": "FAIL" if regressions else "PASS",
        "tolerance": int(tolerance or 0),
        "scores": score_diffs,
        "missing_sections": missing_sections,
        "missing_exports": missing_exports,
        "missing_checks": missing_checks,
        "regressions": regressions,
    }


def _latest_stage_score(validation: dict[str, Any], key: str) -> int:
    stages = validation.get("stage_comparison") or []
    if stages:
        return int((stages[-1] or {}).get(key) or 0)
    return int(validation.get(key) or 0)


def _missing_required_sections(validation: dict[str, Any], required_sections: list[str]) -> list[str]:
    checks = validation.get("checks") or {}
    if checks.get("executive_story_present") and checks.get("no_empty_critical_sections"):
        return []
    # The command-level validation only stores section health as aggregate checks.
    # If those checks fail, report the full required set so CI output is explicit.
    return list(required_sections)


def _missing_required_exports(validation: dict[str, Any], required_exports: list[str]) -> list[str]:
    export_validation = validation.get("export_validation") or {}
    missing = []
    for name in required_exports:
        item = export_validation.get(name) or {}
        if not item.get("present") or not item.get("carries_executive_blocks"):
            missing.append(name)
    return missing
