from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BrandingConfig:
    company: str = "EOR"
    client: str = ""
    confidentiality: str = "Confidencial"
    version: str = "1.0"
    footer: str = "Executive Operation Report"
    header: str = "Executive Document"
    logo_path: str = ""
    primary_color: str = "#0F172A"
    secondary_color: str = "#2563EB"
    accent_color: str = "#F59E0B"


@dataclass(frozen=True)
class Theme:
    name: str = "corporate"
    primary_color: str = "#0F172A"
    secondary_color: str = "#2563EB"
    background_color: str = "#FFFFFF"
    text_color: str = "#111827"
    muted_color: str = "#64748B"
    risk_color: str = "#DC2626"


@dataclass(frozen=True)
class TableModel:
    title: str
    headers: list[str]
    rows: list[list[str]]


@dataclass(frozen=True)
class ChartModel:
    title: str
    chart_type: str
    labels: list[str]
    values: list[float]
    source: str


@dataclass(frozen=True)
class PresentationModel:
    title: str
    subtitle: str
    branding: BrandingConfig
    theme: Theme
    executive_brief: dict[str, Any]
    scorecard: dict[str, Any]
    kpis: list[dict[str, Any]]
    tables: dict[str, list[dict[str, Any]]]
    charts: list[ChartModel]
    rankings: dict[str, list[dict[str, Any]]]
    timeline: dict[str, Any]
    risks: list[dict[str, Any]]
    decisions: list[dict[str, Any]]
    action_plan: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    appendix: dict[str, Any]
    sections: list[str] = field(default_factory=list)

    @classmethod
    def from_output_contract(
        cls,
        output_contract: dict[str, Any],
        *,
        branding: BrandingConfig | None = None,
        theme: Theme | None = None,
    ) -> "PresentationModel":
        _assert_output_contract(output_contract)
        executive_brief = output_contract.get("executive_brief", {})
        diagnosis = output_contract.get("management_diagnosis", {})
        appendix = output_contract.get("analytical_appendix", {})
        tables = output_contract.get("executive_tables", {})
        rankings = output_contract.get("rankings", {})
        title = "Relatorio Executivo EOR"
        subtitle = executive_brief.get("status_geral") or "Publicacao executiva"
        return cls(
            title=title,
            subtitle=subtitle,
            branding=branding or BrandingConfig(),
            theme=theme or Theme(),
            executive_brief=executive_brief,
            scorecard={"score_operacional": executive_brief.get("score_operacional")},
            kpis=list(executive_brief.get("kpis_principais", [])),
            tables=tables,
            charts=[],
            rankings=rankings,
            timeline=appendix.get("timeline", {}),
            risks=list(diagnosis.get("riscos", [])),
            decisions=list(tables.get("decisoes", [])),
            action_plan=list(executive_brief.get("proximas_acoes", [])),
            evidence=list(appendix.get("evidencias", [])),
            appendix=appendix,
            sections=[
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
            ],
        )

    def with_charts(self, charts: list[ChartModel]) -> "PresentationModel":
        return PresentationModel(
            title=self.title,
            subtitle=self.subtitle,
            branding=self.branding,
            theme=self.theme,
            executive_brief=self.executive_brief,
            scorecard=self.scorecard,
            kpis=self.kpis,
            tables=self.tables,
            charts=charts,
            rankings=self.rankings,
            timeline=self.timeline,
            risks=self.risks,
            decisions=self.decisions,
            action_plan=self.action_plan,
            evidence=self.evidence,
            appendix=self.appendix,
            sections=self.sections,
        )


def _assert_output_contract(output_contract: dict[str, Any]) -> None:
    required = {
        "executive_brief",
        "management_diagnosis",
        "analytical_appendix",
        "executive_tables",
        "rankings",
    }
    missing = sorted(required - set(output_contract))
    if missing:
        raise ValueError(f"output_contract incompleto: {', '.join(missing)}")
