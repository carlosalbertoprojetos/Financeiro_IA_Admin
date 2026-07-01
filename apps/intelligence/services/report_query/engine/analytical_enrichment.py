from __future__ import annotations

from collections import Counter, defaultdict
from datetime import timedelta
from typing import Any

from django.utils import timezone

from apps.intelligence.services.checklist.intelligence import analyze_checklists
from apps.intelligence.services.report_query.domain.filters import ReportQueryPayload
from apps.intelligence.services.report_query.engine.card_metrics import get_card_label_names
from apps.intelligence.services.risk_engine.scorer import assess_card_risk
from integrations.trello.models import Action, Card


ACTIVITY_RULES: tuple[dict[str, Any], ...] = (
    {
        "type": "Correcao",
        "keywords": ("bug", "erro", "falha", "corrigir", "correcao", "incidente", "hotfix"),
    },
    {
        "type": "Solicitacao",
        "keywords": ("solicitacao", "pedido", "demanda", "requisicao", "precisa", "necessario"),
    },
    {
        "type": "Infraestrutura",
        "keywords": ("infra", "servidor", "deploy", "ambiente", "docker", "redis", "worker", "storage"),
    },
    {
        "type": "Banco de Dados",
        "keywords": ("banco", "database", "postgres", "sql", "query", "migracao", "indice"),
    },
    {
        "type": "Relatorio",
        "keywords": ("relatorio", "dashboard", "indicador", "kpi", "export", "pdf", "excel"),
    },
    {
        "type": "Automacao",
        "keywords": ("automacao", "sincronizacao", "webhook", "job", "fila", "rotina", "integracao"),
    },
    {
        "type": "Suporte",
        "keywords": ("suporte", "cliente", "atendimento", "duvida", "chamado", "retorno"),
    },
    {
        "type": "Manutencao preventiva",
        "keywords": ("manutencao", "preventiva", "refatorar", "limpeza", "monitoramento", "saude"),
    },
)

STANDARD_REPORT_SECTIONS: tuple[tuple[str, str], ...] = (
    ("executive_summary", "Resumo executivo"),
    ("operational_context", "Contexto operacional"),
    ("volume", "Volume e distribuicao"),
    ("activity_classification", "Tipos de atividade"),
    ("time_metrics", "Tempo e ciclo"),
    ("sla", "SLA e atrasos"),
    ("risk_analysis", "Riscos"),
    ("bottlenecks", "Gargalos"),
    ("quality", "Qualidade operacional"),
    ("communication", "Comunicacao"),
    ("workload", "Carga por responsavel"),
    ("trend_analysis", "Tendencias"),
    ("critical_cards", "Itens criticos"),
    ("recommendations", "Recomendacoes"),
    ("evidence", "Evidencias"),
    ("limitations", "Limitacoes"),
)


def build_report_analytical_layer(
    *,
    cards: list[Card],
    card_rows: list[dict[str, Any]],
    payload: ReportQueryPayload,
    report_data: dict[str, Any],
    metrics_summary: dict[str, Any],
    grouped_summary: dict[str, Any],
) -> dict[str, Any]:
    now = timezone.now()
    actions_by_card = _load_actions_by_card(cards)
    analysis_by_card: list[dict[str, Any]] = []

    for card in cards:
        analysis = _analyze_card(card, actions_by_card.get(card.trello_id, []), now)
        analysis_by_card.append(analysis)

    _merge_card_analysis(card_rows, analysis_by_card)

    volume = _build_volume(cards, analysis_by_card)
    time_metrics = _build_time_metrics(cards, now)
    sla = _build_sla(cards, now)
    quality = _build_quality(cards, analysis_by_card)
    communication = _build_communication(analysis_by_card)
    workload = _build_workload(cards, analysis_by_card)
    trends = _build_trends(cards)
    risks = _build_risks(cards, analysis_by_card, now)
    recommendations = _build_recommendations(cards, analysis_by_card, risks, quality, sla)
    sections = _build_section_coverage(
        cards=cards,
        report_data=report_data,
        metrics_summary=metrics_summary,
        grouped_summary=grouped_summary,
        analysis_by_card=analysis_by_card,
        recommendations=recommendations,
    )
    score = _score_report_quality(sections, cards, recommendations, analysis_by_card)

    return {
        "activity_classification": {
            "categories": volume["by_activity_type"],
            "cards": analysis_by_card,
        },
        "metrics_pack": {
            "volume": volume,
            "time": time_metrics,
            "sla": sla,
            "quality": quality,
            "communication": communication,
            "workload": workload,
            "trends": trends,
            "risks": risks,
        },
        "recommendations": recommendations,
        "quality": score,
        "sections": sections,
        "evidence_policy": {
            "recommendations_require_evidence": True,
            "scores_require_justification": True,
            "empty_text_generates_insight": False,
        },
        "scope": {
            "board_id": payload.board_id,
            "report_type": payload.report_type.value,
            "filters": payload.to_cache_key_dict(),
        },
    }


def _load_actions_by_card(cards: list[Card]) -> dict[str, list[Action]]:
    if not cards:
        return {}
    card_ids = {card.trello_id for card in cards}
    board_pk = cards[0].board_id
    actions = Action.objects.filter(board_id=board_pk).select_related("member").order_by("occurred_at")
    grouped: dict[str, list[Action]] = defaultdict(list)
    for action in actions:
        action_card_id = ((action.raw_json or {}).get("data") or {}).get("card", {}).get("id")
        if action_card_id in card_ids:
            grouped[action_card_id].append(action)
    return grouped


def _analyze_card(card: Card, actions: list[Action], now) -> dict[str, Any]:
    text_sources = _text_sources(card, actions)
    text = " ".join(item["text"] for item in text_sources).lower()
    activity = _classify_activity(text_sources, text)
    checklist = analyze_checklists(card)
    risk = assess_card_risk(card)
    comments = [a for a in actions if a.action_type == "commentCard"]
    stale_days = _days_between(card.last_activity_at or card.updated_at, now)
    description_quality = _description_quality(card.description)
    evidence = activity["evidence"][:5]

    if card.due_at and card.due_at < now and not _is_done(card):
        evidence.append({"source": "due_at", "evidence": "Card vencido e nao concluido"})
    if not card.assignees.exists():
        evidence.append({"source": "assignees", "evidence": "Sem responsavel atribuido"})
    if stale_days is not None and stale_days >= 7 and not _is_done(card):
        evidence.append({"source": "last_activity_at", "evidence": f"Sem atividade ha {stale_days} dias"})
    if checklist.pending_items:
        evidence.append({"source": "checklist", "evidence": f"{checklist.pending_items} itens pendentes"})

    next_action = _suggest_next_action(card, activity["type"], risk.score, checklist.pending_items, stale_days)

    return {
        "card_id": card.trello_id,
        "title": card.title,
        "activity_type": activity["type"],
        "activity_confidence": activity["confidence"],
        "activity_evidence": activity["evidence"],
        "risk_score": risk.score,
        "risk_level": risk.level,
        "description_quality_score": description_quality["score"],
        "description_quality_reason": description_quality["reason"],
        "comment_count": len(comments),
        "checklist_total": checklist.total_items,
        "checklist_pending": checklist.pending_items,
        "stale_days": stale_days,
        "evidence": evidence[:8],
        "next_action": next_action,
    }


def _text_sources(card: Card, actions: list[Action]) -> list[dict[str, str]]:
    sources = [
        {"source": "title", "text": card.title or ""},
        {"source": "description", "text": card.description or ""},
        {"source": "status", "text": card.status or ""},
        {"source": "labels", "text": " ".join(get_card_label_names(card))},
    ]
    for action in actions:
        if action.action_type == "commentCard":
            text = ((action.raw_json or {}).get("data") or {}).get("text") or ""
            if text:
                sources.append({"source": "comment", "text": text})
    return [item for item in sources if item["text"]]


def _classify_activity(text_sources: list[dict[str, str]], text: str) -> dict[str, Any]:
    matches: list[tuple[str, str, str]] = []
    for rule in ACTIVITY_RULES:
        for keyword in rule["keywords"]:
            if keyword in text:
                source = _source_for_keyword(text_sources, keyword)
                matches.append((rule["type"], keyword, source))

    if not matches:
        return {
            "type": "Nao classificado",
            "confidence": 0.2 if text.strip() else 0.0,
            "evidence": [],
        }

    counts = Counter(item[0] for item in matches)
    activity_type, count = counts.most_common(1)[0]
    confidence = min(0.95, 0.45 + count * 0.15)
    evidence = [
        {"source": source, "evidence": keyword}
        for matched_type, keyword, source in matches
        if matched_type == activity_type
    ]
    return {
        "type": activity_type,
        "confidence": round(confidence, 2),
        "evidence": evidence[:5],
    }


def _source_for_keyword(text_sources: list[dict[str, str]], keyword: str) -> str:
    for item in text_sources:
        if keyword in item["text"].lower():
            return item["source"]
    return "text"


def _merge_card_analysis(card_rows: list[dict[str, Any]], analysis_by_card: list[dict[str, Any]]) -> None:
    analysis_map = {item["card_id"]: item for item in analysis_by_card}
    for row in card_rows:
        analysis = analysis_map.get(row.get("card_id"))
        if not analysis:
            continue
        row["activity_type"] = analysis["activity_type"]
        row["activity_confidence"] = analysis["activity_confidence"]
        row["description_quality_score"] = analysis["description_quality_score"]
        row["comment_count"] = analysis["comment_count"]
        row["checklist_pending"] = analysis["checklist_pending"]
        row["evidence"] = analysis["evidence"]
        row["next_action"] = analysis["next_action"]


def _build_volume(cards: list[Card], analysis_by_card: list[dict[str, Any]]) -> dict[str, Any]:
    labels = Counter(label for card in cards for label in get_card_label_names(card))
    lists = Counter(card.board_list.name if card.board_list else "Sem lista" for card in cards)
    statuses = Counter(card.status or "Sem status" for card in cards)
    activity = Counter(item["activity_type"] for item in analysis_by_card)
    return {
        "total_cards": len(cards),
        "by_activity_type": _counter_to_rows(activity),
        "by_label": _counter_to_rows(labels),
        "by_list": _counter_to_rows(lists),
        "by_status": _counter_to_rows(statuses),
    }


def _build_time_metrics(cards: list[Card], now) -> dict[str, Any]:
    open_aging = [_days_between(card.created_at, now) for card in cards if not _is_done(card)]
    open_aging = [value for value in open_aging if value is not None]
    completion_time = [
        _days_between(card.created_at, card.completed_at)
        for card in cards
        if card.completed_at
    ]
    completion_time = [value for value in completion_time if value is not None]
    stale_open = [
        _days_between(card.last_activity_at or card.updated_at, now)
        for card in cards
        if not _is_done(card)
    ]
    stale_open = [value for value in stale_open if value is not None]
    return {
        "avg_open_age_days": _avg(open_aging),
        "max_open_age_days": max(open_aging) if open_aging else None,
        "avg_completion_time_days": _avg(completion_time),
        "avg_days_since_last_activity": _avg(stale_open),
        "stale_cards_7d": sum(1 for value in stale_open if value >= 7),
    }


def _build_sla(cards: list[Card], now) -> dict[str, Any]:
    with_due = [card for card in cards if card.due_at]
    overdue = [
        card
        for card in with_due
        if card.due_at and card.due_at < now and not _is_done(card)
    ]
    completed_late = [
        card
        for card in with_due
        if card.completed_at and card.due_at and card.completed_at > card.due_at
    ]
    in_risk = [
        card
        for card in with_due
        if card.due_at and now <= card.due_at <= now + timedelta(days=2) and not _is_done(card)
    ]
    compliant = len(with_due) - len(overdue) - len(completed_late)
    return {
        "cards_with_due_date": len(with_due),
        "cards_without_due_date": len(cards) - len(with_due),
        "overdue_open_cards": len(overdue),
        "completed_late_cards": len(completed_late),
        "cards_due_in_48h": len(in_risk),
        "compliance_pct": round(compliant / len(with_due) * 100, 1) if with_due else None,
        "critical_card_ids": [card.trello_id for card in overdue[:10]],
    }


def _build_quality(cards: list[Card], analysis_by_card: list[dict[str, Any]]) -> dict[str, Any]:
    descriptions = [item["description_quality_score"] for item in analysis_by_card]
    missing_owner = sum(1 for card in cards if not card.assignees.exists())
    missing_due = sum(1 for card in cards if not card.due_at)
    incomplete_description = sum(1 for card in cards if len((card.description or "").strip()) < 40)
    pending_checklists = sum(1 for item in analysis_by_card if item["checklist_pending"] > 0)
    low_confidence = sum(1 for item in analysis_by_card if item["activity_confidence"] < 0.5)
    return {
        "avg_description_quality_score": _avg(descriptions),
        "missing_owner_count": missing_owner,
        "missing_due_date_count": missing_due,
        "incomplete_description_count": incomplete_description,
        "cards_with_pending_checklists": pending_checklists,
        "low_classification_confidence_count": low_confidence,
    }


def _build_communication(analysis_by_card: list[dict[str, Any]]) -> dict[str, Any]:
    comments = [item["comment_count"] for item in analysis_by_card]
    without_comments = sum(1 for value in comments if value == 0)
    return {
        "total_comments": sum(comments),
        "avg_comments_per_card": _avg(comments),
        "cards_without_comments": without_comments,
        "cards_with_decision_evidence": sum(
            1
            for item in analysis_by_card
            if any("decis" in str(e.get("evidence", "")).lower() for e in item["evidence"])
        ),
    }


def _build_workload(cards: list[Card], analysis_by_card: list[dict[str, Any]]) -> dict[str, Any]:
    risk_by_card = {item["card_id"]: item["risk_score"] for item in analysis_by_card}
    grouped: dict[str, list[Card]] = defaultdict(list)
    for card in cards:
        assignees = list(card.assignees.all())
        if not assignees:
            grouped["Nao atribuido"].append(card)
        for assignee in assignees:
            grouped[assignee.full_name or assignee.username or assignee.trello_id].append(card)

    rows = []
    for name, items in grouped.items():
        risk_values = [risk_by_card.get(card.trello_id, 0) for card in items]
        rows.append(
            {
                "name": name,
                "card_count": len(items),
                "avg_risk_score": _avg(risk_values),
                "overdue_count": sum(1 for card in items if card.due_at and card.due_at < timezone.now() and not _is_done(card)),
            }
        )
    return {"by_member": sorted(rows, key=lambda item: item["card_count"], reverse=True)}


def _build_trends(cards: list[Card]) -> dict[str, Any]:
    by_week: Counter[str] = Counter()
    by_month: Counter[str] = Counter()
    for card in cards:
        dt = card.created_at
        by_week[f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}"] += 1
        by_month[dt.strftime("%Y-%m")] += 1
    return {
        "created_by_week": _counter_to_rows(by_week),
        "created_by_month": _counter_to_rows(by_month),
    }


def _build_risks(cards: list[Card], analysis_by_card: list[dict[str, Any]], now) -> dict[str, Any]:
    risk_rows = []
    for item in analysis_by_card:
        risk_reasons = [e["evidence"] for e in item["evidence"]]
        if item["risk_score"] >= 60 or item["stale_days"] and item["stale_days"] >= 7:
            risk_rows.append(
                {
                    "card_id": item["card_id"],
                    "title": item["title"],
                    "risk_score": item["risk_score"],
                    "risk_level": item["risk_level"],
                    "reasons": risk_reasons,
                    "next_action": item["next_action"],
                }
            )
    categories = Counter(item["activity_type"] for item in analysis_by_card if item["risk_score"] >= 60)
    overdue = [card for card in cards if card.due_at and card.due_at < now and not _is_done(card)]
    return {
        "high_risk_cards": sorted(risk_rows, key=lambda item: item["risk_score"], reverse=True)[:15],
        "risk_by_activity_type": _counter_to_rows(categories),
        "overdue_open_count": len(overdue),
        "delay_probability_pct": round(min(95, len(overdue) / len(cards) * 100 + 15), 1) if cards else None,
    }


def _build_recommendations(
    cards: list[Card],
    analysis_by_card: list[dict[str, Any]],
    risks: dict[str, Any],
    quality: dict[str, Any],
    sla: dict[str, Any],
) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    if risks["high_risk_cards"]:
        top = risks["high_risk_cards"][0]
        recommendations.append(
            {
                "priority": "alta",
                "action": f"Intervir no card {top['card_id']} antes de novos itens.",
                "reason": "Maior risco operacional no recorte analisado.",
                "evidence": top["reasons"][:3],
            }
        )
    if sla["overdue_open_cards"]:
        recommendations.append(
            {
                "priority": "alta",
                "action": "Replanejar cards vencidos e registrar nova data de compromisso.",
                "reason": "Ha itens abertos fora do prazo.",
                "evidence": [f"{sla['overdue_open_cards']} cards vencidos"],
            }
        )
    if quality["missing_owner_count"]:
        recommendations.append(
            {
                "priority": "media",
                "action": "Atribuir responsaveis para todos os cards sem dono.",
                "reason": "Cards sem responsavel reduzem rastreabilidade e execucao.",
                "evidence": [f"{quality['missing_owner_count']} cards sem responsavel"],
            }
        )
    if quality["incomplete_description_count"]:
        recommendations.append(
            {
                "priority": "media",
                "action": "Completar descricoes com contexto, objetivo, criterio de aceite e proximo passo.",
                "reason": "Descricoes curtas reduzem a qualidade analitica do relatorio.",
                "evidence": [f"{quality['incomplete_description_count']} descricoes incompletas"],
            }
        )
    low_confidence_cards = [
        item["card_id"] for item in analysis_by_card if item["activity_confidence"] < 0.5
    ]
    if low_confidence_cards:
        recommendations.append(
            {
                "priority": "baixa",
                "action": "Padronizar titulos, etiquetas ou descricoes dos cards de baixa confianca.",
                "reason": "A classificacao precisa de evidencias textuais melhores.",
                "evidence": low_confidence_cards[:5],
            }
        )
    return recommendations[:8]


def _build_section_coverage(
    *,
    cards: list[Card],
    report_data: dict[str, Any],
    metrics_summary: dict[str, Any],
    grouped_summary: dict[str, Any],
    analysis_by_card: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
) -> dict[str, Any]:
    evidence_count = sum(len(item["evidence"]) for item in analysis_by_card)
    checks = {
        "executive_summary": bool(report_data),
        "operational_context": bool(cards),
        "volume": bool(cards),
        "activity_classification": any(item["activity_type"] != "Nao classificado" for item in analysis_by_card),
        "time_metrics": bool(metrics_summary),
        "sla": bool(metrics_summary.get("sla")) or any(card.due_at for card in cards),
        "risk_analysis": any(item["risk_score"] is not None for item in analysis_by_card),
        "bottlenecks": bool(grouped_summary),
        "quality": bool(cards),
        "communication": any(item["comment_count"] for item in analysis_by_card),
        "workload": any(card.assignees.exists() for card in cards),
        "trend_analysis": bool(cards),
        "critical_cards": any(item["risk_score"] >= 60 for item in analysis_by_card),
        "recommendations": bool(recommendations),
        "evidence": evidence_count > 0,
        "limitations": True,
    }
    covered = [
        {"key": key, "name": name, "present": checks[key]}
        for key, name in STANDARD_REPORT_SECTIONS
    ]
    return {
        "standard_sections": covered,
        "covered_count": sum(1 for item in covered if item["present"]),
        "total_count": len(covered),
        "missing_sections": [item for item in covered if not item["present"]],
    }


def _score_report_quality(
    sections: dict[str, Any],
    cards: list[Card],
    recommendations: list[dict[str, Any]],
    analysis_by_card: list[dict[str, Any]],
) -> dict[str, Any]:
    section_score = sections["covered_count"] / sections["total_count"] * 40 if sections["total_count"] else 0
    evidence_cards = sum(1 for item in analysis_by_card if item["evidence"])
    evidence_score = evidence_cards / len(cards) * 25 if cards else 0
    recommendation_score = min(15, len(recommendations) * 4)
    confidence_values = [item["activity_confidence"] for item in analysis_by_card]
    confidence_score = (_avg(confidence_values) or 0) * 20
    score = round(min(100, section_score + evidence_score + recommendation_score + confidence_score), 1)
    if score >= 85:
        label = "excelente"
    elif score >= 70:
        label = "bom"
    elif score >= 50:
        label = "regular"
    else:
        label = "baixo"
    return {
        "report_quality_score": score,
        "label": label,
        "justification": [
            f"{sections['covered_count']} de {sections['total_count']} secoes analiticas cobertas",
            f"{evidence_cards} de {len(cards)} cards com evidencias rastreaveis",
            f"{len(recommendations)} recomendacoes com evidencia",
        ],
        "missing_sections": sections["missing_sections"],
        "improvement_suggestions": _quality_suggestions(sections, evidence_cards, cards, recommendations),
    }


def _quality_suggestions(
    sections: dict[str, Any],
    evidence_cards: int,
    cards: list[Card],
    recommendations: list[dict[str, Any]],
) -> list[str]:
    suggestions = []
    if sections["missing_sections"]:
        missing_names = ", ".join(item["name"] for item in sections["missing_sections"][:4])
        suggestions.append(f"Adicionar dados para cobrir secoes ausentes: {missing_names}.")
    if cards and evidence_cards < len(cards):
        suggestions.append("Melhorar descricoes, comentarios, etiquetas ou checklists dos cards sem evidencia.")
    if not recommendations:
        suggestions.append("Registrar prazos, responsaveis e riscos para permitir recomendacoes acionaveis.")
    return suggestions


def _suggest_next_action(card: Card, activity_type: str, risk_score: int, pending_checklist: int, stale_days: int | None) -> str:
    if risk_score >= 70:
        return "Revisar risco, responsavel, prazo e proximo passo ainda hoje."
    if card.due_at and card.due_at < timezone.now() and not _is_done(card):
        return "Atualizar compromisso e remover bloqueios do item vencido."
    if pending_checklist:
        return "Concluir ou replanejar itens pendentes do checklist."
    if stale_days is not None and stale_days >= 7:
        return "Solicitar atualizacao do responsavel e registrar decisao."
    if activity_type == "Nao classificado":
        return "Adicionar descricao ou etiqueta para melhorar a leitura executiva."
    return "Manter acompanhamento e registrar a proxima decisao operacional."


def _description_quality(description: str) -> dict[str, Any]:
    text = (description or "").strip()
    if not text:
        return {"score": 0, "reason": "Descricao vazia"}
    score = 25
    if len(text) >= 80:
        score += 25
    if any(token in text.lower() for token in ("objetivo", "criterio", "prazo", "responsavel", "risco")):
        score += 25
    if any(token in text.lower() for token in ("proximo", "acao", "pendente", "decisao")):
        score += 25
    if score >= 75:
        reason = "Descricao contem contexto suficiente para analise"
    elif score >= 50:
        reason = "Descricao parcial, mas utilizavel"
    else:
        reason = "Descricao curta ou pouco acionavel"
    return {"score": min(100, score), "reason": reason}


def _is_done(card: Card) -> bool:
    status = (card.status or "").lower()
    return card.is_closed or status in {"done", "completed", "concluido", "concluído", "finalizado"}


def _days_between(start, end) -> int | None:
    if not start or not end:
        return None
    return max(0, (end - start).days)


def _avg(values: list[int | float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 1)


def _counter_to_rows(counter: Counter[str]) -> list[dict[str, Any]]:
    return [
        {"name": name, "count": count}
        for name, count in counter.most_common()
    ]
