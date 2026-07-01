from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from apps.intelligence.services.description_intelligence.parser import LINK_RE


StructuredDescriptionDict = dict[str, Any]

METRIC_RE = re.compile(
    r"(?<!\w)(?:R\$\s*)?\d+(?:[.,]\d+)?\s*(?:%|h|hs|horas?|dias?|cards?|itens?|tarefas?)?",
    re.I,
)
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.+?)\s*$")


SECTION_ALIASES = {
    "data_solicitacao": (
        "data da solicitacao",
        "data solicitacao",
        "data de solicitacao",
        "solicitacao",
    ),
    "objetivo": ("objetivo", "objetivos", "finalidade"),
    "contexto": ("contexto", "cenario", "situacao", "observacao", "observacoes"),
    "atividades": ("atividades", "atividade", "acoes", "acao", "tarefas", "passos"),
    "resultado_esperado": (
        "resultado esperado",
        "resultados esperados",
        "expectativa",
        "saida esperada",
    ),
    "riscos": ("risco", "riscos", "impedimento", "impedimentos", "bloqueio", "bloqueios"),
    "criterios_conclusao": (
        "criterio de conclusao",
        "criterios de conclusao",
        "criterio de aceite",
        "criterios de aceite",
        "criterio conclusao",
        "criterios conclusao",
    ),
    "resultado_obtido": (
        "resultado obtido",
        "resultados obtidos",
        "resultado",
        "entrega realizada",
    ),
    "evidencias": ("evidencia", "evidencias", "comprovacao", "comprovacoes", "links de evidencia"),
}

LIST_FIELDS = {"atividades", "riscos", "criterios_conclusao", "evidencias"}
TEXT_FIELDS = {"data_solicitacao", "objetivo", "contexto", "resultado_esperado", "resultado_obtido"}


@dataclass
class StructuredDescription:
    data_solicitacao: str | None = None
    objetivo: str | None = None
    contexto: str | None = None
    atividades: list[str] = field(default_factory=list)
    resultado_esperado: str | None = None
    riscos: list[str] = field(default_factory=list)
    criterios_conclusao: list[str] = field(default_factory=list)
    resultado_obtido: str | None = None
    evidencias: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    metricas: list[str] = field(default_factory=list)
    raw_description: str = ""

    def to_dict(self) -> StructuredDescriptionDict:
        return {
            "data_solicitacao": self.data_solicitacao,
            "objetivo": self.objetivo,
            "contexto": self.contexto,
            "atividades": list(self.atividades),
            "resultado_esperado": self.resultado_esperado,
            "riscos": list(self.riscos),
            "criterios_conclusao": list(self.criterios_conclusao),
            "resultado_obtido": self.resultado_obtido,
            "evidencias": list(self.evidencias),
            "links": list(self.links),
            "metricas": list(self.metricas),
            "raw_description": self.raw_description,
        }


def parse_structured_description(text: str | None) -> StructuredDescriptionDict:
    """
    Parse the preferred Trello management-description format.

    The parser is permissive: missing sections remain None or empty lists, title
    variations are accepted, and no business fact is inferred from absent text.
    """
    raw = text or ""
    normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
    result = StructuredDescription(raw_description=raw)
    sections: dict[str, list[str]] = {key: [] for key in SECTION_ALIASES}
    current_section: str | None = None

    for raw_line in normalized.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        heading, inline_value = _split_heading(line)
        if heading:
            current_section = heading
            if inline_value:
                sections[heading].append(inline_value)
            continue

        if current_section:
            sections[current_section].append(line)

    _populate_text_fields(result, sections)
    _populate_list_fields(result, sections)
    result.links = _dedupe(_extract_links(normalized))
    result.metricas = _dedupe(_extract_metrics(normalized))

    if not result.riscos:
        result.riscos = _keyword_lines(normalized, ("risco", "riscos", "bloqueio", "impedimento"))
    if not result.evidencias:
        result.evidencias = _keyword_lines(normalized, ("evidencia", "evidencias", "comprovacao"))

    return result.to_dict()


def compute_documentation_completeness(
    description_sections: StructuredDescriptionDict,
    *,
    has_checklist: bool = False,
    has_owner: bool = False,
) -> int:
    """Score the 10 management-documentation fields requested for reports."""
    checks = [
        bool(description_sections.get("objetivo")),
        bool(description_sections.get("contexto")),
        bool(description_sections.get("atividades")),
        bool(description_sections.get("resultado_esperado")),
        bool(description_sections.get("riscos")),
        bool(description_sections.get("criterios_conclusao")),
        bool(description_sections.get("resultado_obtido")),
        bool(description_sections.get("evidencias")),
        has_checklist,
        has_owner,
    ]
    return int(round(sum(1 for item in checks if item) / len(checks) * 100))


def _populate_text_fields(result: StructuredDescription, sections: dict[str, list[str]]) -> None:
    for field_name in TEXT_FIELDS:
        value = _join_text(sections.get(field_name, []))
        setattr(result, field_name, value or None)


def _populate_list_fields(result: StructuredDescription, sections: dict[str, list[str]]) -> None:
    for field_name in LIST_FIELDS:
        values = _list_items(sections.get(field_name, []))
        setattr(result, field_name, values)


def _split_heading(line: str) -> tuple[str | None, str]:
    cleaned = line.strip().lstrip("#").strip()
    candidates = [cleaned]
    if ":" in cleaned:
        title, value = cleaned.split(":", 1)
        candidates.insert(0, title.strip())
        inline_value = value.strip()
    else:
        inline_value = ""

    for candidate in candidates:
        field_name = _field_for_heading(candidate)
        if field_name:
            return field_name, inline_value
    return None, ""


def _field_for_heading(value: str) -> str | None:
    normalized = _normalize(value.rstrip(":"))
    for field_name, aliases in SECTION_ALIASES.items():
        if normalized in {_normalize(alias) for alias in aliases}:
            return field_name
    return None


def _normalize(value: str) -> str:
    without_accents = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(ch for ch in without_accents if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.lower()).strip()


def _join_text(lines: list[str]) -> str:
    cleaned = [_strip_bullet(line) for line in lines if _strip_bullet(line)]
    return "\n".join(cleaned).strip()


def _list_items(lines: list[str]) -> list[str]:
    items: list[str] = []
    for line in lines:
        text = _strip_bullet(line)
        if text:
            items.append(text)
    return _dedupe(items)


def _strip_bullet(line: str) -> str:
    match = BULLET_RE.match(line)
    return (match.group(1) if match else line).strip()


def _extract_links(text: str) -> list[str]:
    return [match.group(0).rstrip(".,;") for match in LINK_RE.finditer(text)]


def _extract_metrics(text: str) -> list[str]:
    values = []
    for match in METRIC_RE.finditer(text):
        value = match.group(0).strip()
        if any(ch.isdigit() for ch in value):
            values.append(value)
    return values


def _keyword_lines(text: str, keywords: tuple[str, ...]) -> list[str]:
    normalized_keywords = tuple(_normalize(keyword) for keyword in keywords)
    values: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        normalized_line = _normalize(stripped)
        if stripped and any(keyword in normalized_line for keyword in normalized_keywords):
            values.append(_strip_bullet(stripped))
    return _dedupe(values)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
