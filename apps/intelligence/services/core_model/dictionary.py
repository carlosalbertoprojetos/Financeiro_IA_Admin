from __future__ import annotations

from typing import Any

SEMANTIC_DICTIONARY: dict[str, dict[str, Any]] = {
    "INCIDENT": {
        "term": "INCIDENT",
        "definition": "Qualquer evento que gera impacto negativo no fluxo operacional",
        "canonical_entity": "INCIDENT",
        "signals": ["atraso", "erro", "bloqueio", "retrabalho", "overdue"],
        "layer": "semantic",
    },
    "DELIVERY": {
        "term": "DELIVERY",
        "definition": "Conclusão de entrega de valor operacional ao stakeholder",
        "canonical_entity": "DELIVERY",
        "signals": ["conclusão", "deploy", "envio", "finalização", "completed"],
        "layer": "semantic",
    },
    "RISK": {
        "term": "RISK",
        "definition": "Exposição operacional a falhas, atrasos ou dependências críticas",
        "canonical_entity": "RISK_EVENT",
        "signals": ["dependência externa", "atraso recorrente", "sobrecarga"],
        "layer": "semantic",
    },
    "SLA": {
        "term": "SLA",
        "definition": "Compromisso temporal de entrega vinculado a due date",
        "canonical_entity": "SLA_CONTRACT",
        "signals": ["due_date", "prazo", "compliance"],
        "layer": "query_engine",
    },
    "BLOCKER": {
        "term": "BLOCKER",
        "definition": "Impedimento que interrompe o fluxo de trabalho",
        "canonical_entity": "BOTTLENECK",
        "signals": ["bloqueado", "blocked", "stagnant", "excessive_movements"],
        "layer": "semantic",
    },
    "PROJECT": {
        "term": "PROJECT",
        "definition": "Conjunto coerente de work items com prefixo ou categoria comum",
        "canonical_entity": "PROJECT",
        "signals": ["prefix", "category", "title_prefix"],
        "layer": "semantic",
    },
}


def get_term(term: str) -> dict[str, Any] | None:
    return SEMANTIC_DICTIONARY.get(term.upper())


def resolve_canonical_entity(term: str) -> str | None:
    entry = get_term(term)
    return entry.get("canonical_entity") if entry else None


def all_terms() -> list[str]:
    return sorted(SEMANTIC_DICTIONARY.keys())
