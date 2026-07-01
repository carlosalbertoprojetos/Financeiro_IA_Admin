from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from apps.intelligence.services.description_intelligence.classifier import classify_description
from apps.intelligence.services.description_intelligence.entity_extractor import extract_entities
from apps.intelligence.services.description_intelligence.event_extractor import extract_events
from apps.intelligence.services.description_intelligence.parser import Evidence, ParsedDescription, parse_description
from apps.intelligence.services.description_intelligence.quality_score import compute_description_quality
from integrations.trello.models import Card


SUMMARY_FIELDS = {
    "objetivo": ("objetivo", "finalidade"),
    "contexto": ("contexto", "observacao", "observação"),
    "problema": ("problema", "erro", "falha", "incidente"),
    "solucao": ("solucao", "solução", "acao", "ação", "procedimento"),
    "resultado": ("resultado", "resultado_obtido"),
    "impacto": ("impacto", "risco"),
    "solicitacao": ("solicitacao", "solicitação"),
    "resultado_esperado": ("resultado_esperado",),
    "bloqueios": ("bloqueio", "bloqueios", "impedimento"),
    "dependencias": ("dependencia", "dependência", "dependencias", "dependências"),
    "licoes_aprendidas": ("licoes_aprendidas", "lições_aprendidas", "licao", "lição"),
}


def analyze_card_description(card: Card, *, persist_timeline: bool = False) -> dict[str, Any]:
    result = analyze_description(card.description or "", source=f"trello.card.description:{card.trello_id}")
    result["card_id"] = card.trello_id
    result["card_title"] = card.title
    if persist_timeline:
        from apps.intelligence.services.description_intelligence.event_extractor import persist_description_events

        result["timeline_events_created"] = persist_description_events(card, result["_events"])
    result.pop("_events", None)
    return result


def analyze_description(text: str, *, source: str = "trello.card.description") -> dict[str, Any]:
    parsed = parse_description(text, source=source)
    classifications = classify_description(parsed)
    entities = extract_entities(parsed)
    events = extract_events(parsed)
    quality = compute_description_quality(parsed, entities_count=len(entities), events=events)
    expanded_summary = build_expanded_summary(parsed)

    return {
        "parser": parsed.to_dict(),
        "expanded_summary": expanded_summary,
        "classifications": [item.to_dict() for item in classifications],
        "entities": [item.to_dict() for item in entities],
        "events": [item.to_dict() for item in events],
        "quality": quality.to_dict(),
        "kpis": compute_description_kpis(
            classifications=[item.to_dict() for item in classifications],
            entities=[item.to_dict() for item in entities],
            events=[item.to_dict() for item in events],
            quality_score=quality.score,
        ),
        "_events": events,
    }


def build_expanded_summary(parsed: ParsedDescription) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for field, aliases in SUMMARY_FIELDS.items():
        evidence = _first_matching_evidence(parsed, aliases)
        summary[field] = evidence.to_dict() if evidence else None
    return summary


def aggregate_description_intelligence(cards: list[Card]) -> dict[str, Any]:
    analyses = [analyze_card_description(card) for card in cards]
    categories = Counter(
        item["category"]
        for analysis in analyses
        for item in analysis["classifications"]
        if item["category"] != "Outra"
    )
    by_entity_type = Counter(
        item["entity_type"]
        for analysis in analyses
        for item in analysis["entities"]
    )
    quality_scores = [analysis["quality"]["score"] for analysis in analyses]
    event_counts = Counter(
        item["event_type"]
        for analysis in analyses
        for item in analysis["events"]
    )

    return {
        "cards_analyzed": len(cards),
        "cards_with_description": sum(1 for card in cards if (card.description or "").strip()),
        "categories": dict(categories),
        "entities_by_type": dict(by_entity_type),
        "events_by_type": dict(event_counts),
        "avg_description_quality_score": round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else 0,
        "analyses": analyses,
        "dashboards": build_description_dashboards(analyses),
    }


def compute_description_kpis(
    *,
    classifications: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    events: list[dict[str, Any]],
    quality_score: int,
) -> dict[str, Any]:
    categories = {item["category"] for item in classifications}
    entity_types = {item["entity_type"] for item in entities}
    corrective = len(categories & {"Correção", "Corretiva", "Bug", "Incidente", "Reparo"})
    preventive = len(categories & {"Preventiva", "Monitoramento", "Backup", "Segurança"})
    improvement = len(categories & {"Melhoria", "Feature", "Automação", "Documentação"})
    infra = len(categories & {"Infraestrutura", "Rede", "Servidor", "Banco de Dados", "Backup", "Segurança"})

    return {
        "infrastructure_workload_index": min(100, infra * 20),
        "maintenance_index": min(100, (corrective + preventive) * 15),
        "incident_density": min(100, len(categories & {"Incidente", "Bug"}) * 30),
        "correction_rate": min(100, corrective * 20),
        "improvement_rate": min(100, improvement * 20),
        "preventive_vs_corrective_ratio": round(preventive / max(corrective, 1), 2),
        "operational_complexity_score": min(100, len(entity_types) * 8 + len(events) * 5),
        "description_completeness": quality_score,
        "operational_documentation_score": quality_score,
        "knowledge_capture_score": min(100, quality_score + (20 if "RESULT_RECORDED" in {e["event_type"] for e in events} else 0)),
    }


def build_description_dashboards(analyses: list[dict[str, Any]]) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for analysis in analyses:
        categories = {item["category"] for item in analysis["classifications"]}
        if categories & {"Infraestrutura", "Rede", "Servidor", "Banco de Dados", "Backup", "Segurança"}:
            buckets["infraestrutura"].append(analysis)
        if categories & {"Atendimento", "Solicitação", "Treinamento"}:
            buckets["suporte"].append(analysis)
        if "Projeto" in categories:
            buckets["projetos"].append(analysis)
        if categories & {"Melhoria", "Feature", "Automação"}:
            buckets["melhorias"].append(analysis)
        if categories & {"Incidente", "Bug"}:
            buckets["incidentes"].append(analysis)
        if "Preventiva" in categories:
            buckets["preventiva"].append(analysis)
        if categories & {"Corretiva", "Correção", "Reparo"}:
            buckets["corretiva"].append(analysis)
        buckets["executivo"].append(analysis)

    return {name: _dashboard_payload(name, items) for name, items in buckets.items()}


def _dashboard_payload(name: str, analyses: list[dict[str, Any]]) -> dict[str, Any]:
    top_categories = Counter(
        item["category"]
        for analysis in analyses
        for item in analysis["classifications"]
    ).most_common(10)
    top_systems = Counter(
        item["value"]
        for analysis in analyses
        for item in analysis["entities"]
        if item["entity_type"] in ("sistema", "servico", "host", "database")
    ).most_common(10)
    risks = [
        analysis["expanded_summary"]["impact"]
        for analysis in analyses
        if analysis["expanded_summary"].get("impact")
    ]
    return {
        "dashboard": name,
        "cards": len(analyses),
        "kpis": _aggregate_kpis(analyses),
        "top_categories": top_categories,
        "top_systems": top_systems,
        "top_risks": risks[:10],
        "timeline": [
            event
            for analysis in analyses
            for event in analysis["events"]
        ][:50],
        "heatmaps": {"category_by_quality": _quality_by_category(analyses)},
        "trends": {"source": "description_intelligence", "status": "available_after_time_series_accumulation"},
    }


def _aggregate_kpis(analyses: list[dict[str, Any]]) -> dict[str, float]:
    if not analyses:
        return {}
    keys = analyses[0]["kpis"].keys()
    return {
        key: round(sum(float(item["kpis"].get(key, 0)) for item in analyses) / len(analyses), 2)
        for key in keys
    }


def _quality_by_category(analyses: list[dict[str, Any]]) -> dict[str, float]:
    values: dict[str, list[int]] = defaultdict(list)
    for analysis in analyses:
        for classification in analysis["classifications"]:
            values[classification["category"]].append(analysis["quality"]["score"])
    return {
        category: round(sum(scores) / len(scores), 1)
        for category, scores in values.items()
        if scores
    }


def _first_matching_evidence(parsed: ParsedDescription, aliases: tuple[str, ...]) -> Evidence | None:
    for alias in aliases:
        normalized_alias = alias.replace("ç", "c").replace("ã", "a")
        for key, values in parsed.key_values.items():
            normalized_key = key.replace("ç", "c").replace("ã", "a")
            if normalized_alias in normalized_key and values:
                return values[0]
        for key, values in parsed.sections.items():
            normalized_key = key.replace("ç", "c").replace("ã", "a")
            if normalized_alias in normalized_key and len(values) > 1:
                return values[1]
    return None
