from __future__ import annotations

from typing import Any


def build_executive_story(
    *,
    summary: dict[str, Any],
    metrics: dict[str, Any],
    analytical_enrichment: dict[str, Any],
    executive_narrative: dict[str, Any],
    discovery: dict[str, Any],
    risks: dict[str, Any],
    recommendations: list[dict[str, Any]],
) -> dict[str, Any]:
    evidence_map = _build_evidence_map(
        analytical_enrichment=analytical_enrichment,
        executive_narrative=executive_narrative,
        discovery=discovery,
        risks=risks,
        recommendations=recommendations,
    )
    if not evidence_map:
        return _empty_story()

    drivers = _top_drivers(executive_narrative, discovery)
    decisions = _decision_ready_summary(executive_narrative, discovery, recommendations)
    action_plan = _action_plan(executive_narrative, discovery, decisions)
    root_causes = _root_causes(executive_narrative, discovery)
    business_implications = _business_implications(executive_narrative, discovery, risks)
    what_changed = _what_changed(discovery, analytical_enrichment)
    headline = _headline(drivers, discovery, risks)
    period_story = _period_story(summary, metrics, headline, what_changed, drivers)
    quality = _story_quality(
        headline=headline,
        period_story=period_story,
        drivers=drivers,
        root_causes=root_causes,
        business_implications=business_implications,
        decisions=decisions,
        action_plan=action_plan,
        evidence_map=evidence_map,
    )

    return {
        "headline": headline,
        "period_story": period_story,
        "story_structure": {
            "contexto_periodo": _section("Contexto do período", period_story, evidence_map[:3]),
            "principais_mudancas": _section("Principais mudanças", _join_titles(what_changed), _evidence_from_items(what_changed)),
            "fatores_resultado": _section("Fatores que explicam o resultado", _join_titles(drivers), _evidence_from_items(drivers)),
            "causas_provaveis": _section("Causas prováveis", _join_titles(root_causes), _evidence_from_items(root_causes)),
            "impactos_operacionais": _section("Impactos operacionais", _join_titles(business_implications), _evidence_from_items(business_implications)),
            "riscos_se_nada_mudar": _section("Riscos se nada mudar", _risk_if_no_change(risks, discovery), _risk_evidence(risks, discovery)),
            "oportunidades": _section("Oportunidades", _join_titles(discovery.get("opportunities", [])[:3]), _evidence_from_items(discovery.get("opportunities", [])[:3])),
            "decisoes_prioritarias": _section("Decisões prioritárias", _join_titles(decisions, key="decision"), _evidence_from_items(decisions)),
            "plano_acao": _section("Plano de ação", _join_titles(action_plan, key="action"), _evidence_from_items(action_plan)),
        },
        "what_changed": what_changed,
        "key_drivers": drivers,
        "root_causes": root_causes,
        "business_implications": business_implications,
        "priority_decisions": decisions,
        "decision_ready_summary": decisions[:3],
        "action_plan": action_plan,
        "story_confidence": quality["confidence"],
        "executive_story_quality_score": quality,
        "evidence_map": evidence_map,
        "generated": True,
    }


def _empty_story() -> dict[str, Any]:
    return {
        "headline": "",
        "period_story": "",
        "story_structure": {},
        "what_changed": [],
        "key_drivers": [],
        "root_causes": [],
        "business_implications": [],
        "priority_decisions": [],
        "decision_ready_summary": [],
        "action_plan": [],
        "story_confidence": 0,
        "executive_story_quality_score": {
            "score": 0,
            "label": "baixo",
            "confidence": 0,
            "criteria": {},
            "justification": ["Historia nao gerada por falta de evidencias."],
        },
        "evidence_map": [],
        "generated": False,
    }


def _build_evidence_map(
    *,
    analytical_enrichment: dict[str, Any],
    executive_narrative: dict[str, Any],
    discovery: dict[str, Any],
    risks: dict[str, Any],
    recommendations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for item in executive_narrative.get("insights", []):
        evidence.extend(_evidence_entries("executive_narrative.insights", item.get("title"), item.get("evidence", [])))
    for item in discovery.get("executive_highlights", []):
        evidence.extend(_evidence_entries("discovery.executive_highlights", item.get("title"), item.get("evidence", [])))
    for item in discovery.get("executive_surprises", []):
        evidence.extend(_evidence_entries("discovery.executive_surprises", item.get("text"), item.get("evidence", [])))
    for item in risks.get("high_risk_cards", []):
        evidence.extend(_evidence_entries("analytical.metrics_pack.risks.high_risk_cards", item.get("card_id"), item.get("reasons", [])))
    for item in recommendations:
        evidence.extend(_evidence_entries("analytical.recommendations", item.get("action"), item.get("evidence", [])))

    metrics_pack = analytical_enrichment.get("metrics_pack", {})
    sla = metrics_pack.get("sla", {})
    quality = metrics_pack.get("quality", {})
    for key in ("overdue_open_cards", "cards_without_due_date", "cards_due_in_48h"):
        if sla.get(key):
            evidence.append({"source": f"metrics_pack.sla.{key}", "claim": key, "evidence": str(sla[key])})
    for key in ("missing_owner_count", "incomplete_description_count", "cards_with_pending_checklists"):
        if quality.get(key):
            evidence.append({"source": f"metrics_pack.quality.{key}", "claim": key, "evidence": str(quality[key])})
    return _dedupe_evidence(evidence)


def _top_drivers(executive_narrative: dict[str, Any], discovery: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for item in discovery.get("executive_highlights", []):
        candidates.append(
            {
                "title": item.get("title"),
                "explanation": _driver_explanation(item),
                "evidence": item.get("evidence", []),
                "impact": item.get("impact", 0),
                "recommended_action": _action_from_highlight(item),
                "confidence": item.get("confidence", 0.6),
                "_rank": (
                    int(item.get("impact") or 0),
                    _severity_weight(item.get("severity")),
                    len(item.get("evidence", [])),
                    int(item.get("impact") or 0),
                ),
            }
        )
    for item in executive_narrative.get("insights", []):
        candidates.append(
            {
                "title": item.get("title"),
                "explanation": item.get("business_impact"),
                "evidence": item.get("evidence", []),
                "impact": item.get("_rank", {}).get("impact", 0),
                "recommended_action": item.get("recommended_action"),
                "confidence": item.get("confidence", 0.6),
                "_rank": (
                    item.get("_rank", {}).get("impact", 0),
                    _severity_weight(item.get("severity")),
                    item.get("_rank", {}).get("recurrence", 0),
                    item.get("_rank", {}).get("risk", 0),
                ),
            }
        )
    ranked = sorted(_dedupe_by_title(candidates), key=lambda item: item["_rank"], reverse=True)
    return [_public_driver(item) for item in ranked[:3] if item.get("evidence")]


def _decision_ready_summary(
    executive_narrative: dict[str, Any],
    discovery: dict[str, Any],
    recommendations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    narrative_decisions = executive_narrative.get("management_decisions", [])
    for decision in narrative_decisions:
        decisions.append(
            {
                "decision": decision.get("decision"),
                "reason": decision.get("reason"),
                "evidence": [decision.get("reason")] if decision.get("reason") else [],
                "consequence_if_no_action": _consequence(decision.get("urgency")),
                "urgency": decision.get("urgency", "media"),
                "suggested_owner": decision.get("suggested_owner", "Gestor operacional"),
                "suggested_deadline": decision.get("suggested_deadline", "Proximo ciclo"),
            }
        )

    for item in discovery.get("opportunities", []):
        decisions.append(
            {
                "decision": item.get("recommended_action"),
                "reason": item.get("potential_gain"),
                "evidence": item.get("evidence", []),
                "consequence_if_no_action": "A oportunidade tende a continuar como perda operacional recorrente.",
                "urgency": "media",
                "suggested_owner": "Gestor operacional",
                "suggested_deadline": "7 dias",
            }
        )

    for item in recommendations:
        evidence = item.get("evidence", [])
        if evidence:
            decisions.append(
                {
                    "decision": item.get("action"),
                    "reason": item.get("reason"),
                    "evidence": evidence,
                    "consequence_if_no_action": "O risco identificado permanece sem tratamento gerencial.",
                    "urgency": item.get("priority", "media"),
                    "suggested_owner": "Gestor operacional",
                    "suggested_deadline": "Proximo ciclo",
                }
            )
    return _dedupe_decisions([item for item in decisions if item.get("decision") and item.get("evidence")])[:3]


def _action_plan(
    executive_narrative: dict[str, Any],
    discovery: dict[str, Any],
    decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for decision in decisions:
        actions.append(
            {
                "action": decision["decision"],
                "owner": decision["suggested_owner"],
                "deadline": decision["suggested_deadline"],
                "evidence": decision["evidence"],
                "expected_result": decision.get("reason") or "Reduzir risco operacional.",
            }
        )
    for item in executive_narrative.get("next_actions", []):
        evidence = item.get("evidence", [])
        if evidence:
            actions.append(
                {
                    "action": item.get("action"),
                    "owner": "Responsavel operacional",
                    "deadline": "24h" if item.get("urgency") == "alta" else "Proximo ciclo",
                    "evidence": evidence,
                    "expected_result": "Executar a proxima acao indicada pelo relatorio.",
                }
            )
    if not actions and discovery.get("anomalies"):
        top = discovery["anomalies"][0]
        actions.append(
            {
                "action": f"Tratar anomalia: {top.get('title')}",
                "owner": "Gestor operacional",
                "deadline": "24h",
                "evidence": top.get("evidence", []),
                "expected_result": "Reduzir a anomalia de maior impacto.",
            }
        )
    return _dedupe_actions(actions)[:7]


def _root_causes(executive_narrative: dict[str, Any], discovery: dict[str, Any]) -> list[dict[str, Any]]:
    causes = []
    for item in executive_narrative.get("root_cause_hypotheses", [])[:3]:
        causes.append(
            {
                "title": item.get("hypothesis"),
                "explanation": item.get("how_to_validate"),
                "evidence": item.get("evidence", []),
                "confidence": item.get("confidence", 0.6),
            }
        )
    for item in discovery.get("correlations", [])[:2]:
        causes.append(
            {
                "title": item.get("title"),
                "explanation": "Correlacao observada no recorte; validar antes de tratar como causa.",
                "evidence": item.get("evidence", []),
                "confidence": item.get("confidence", 0.6),
            }
        )
    return [item for item in _dedupe_by_title(causes) if item.get("evidence")][:4]


def _business_implications(
    executive_narrative: dict[str, Any],
    discovery: dict[str, Any],
    risks: dict[str, Any],
) -> list[dict[str, Any]]:
    implications = []
    for item in executive_narrative.get("insights", [])[:4]:
        implications.append(
            {
                "title": item.get("affected_area"),
                "explanation": item.get("business_impact"),
                "evidence": item.get("evidence", []),
                "severity": item.get("severity"),
            }
        )
    for item in discovery.get("what_happens_next", [])[:3]:
        implications.append(
            {
                "title": "Cenario provavel",
                "explanation": item.get("scenario"),
                "evidence": item.get("basis", []),
                "severity": "media",
            }
        )
    if risks.get("high_risk_cards"):
        implications.append(
            {
                "title": "Risco operacional",
                "explanation": f"{len(risks['high_risk_cards'])} cards exigem atencao por risco elevado.",
                "evidence": [item.get("card_id") for item in risks["high_risk_cards"][:5]],
                "severity": "alta",
            }
        )
    return [item for item in _dedupe_by_title(implications) if item.get("evidence")][:5]


def _what_changed(discovery: dict[str, Any], analytical_enrichment: dict[str, Any]) -> list[dict[str, Any]]:
    changes = []
    for item in discovery.get("patterns", []):
        if item.get("kind") == "trend" or "Concentracao" in str(item.get("title")):
            changes.append(
                {
                    "title": item.get("title"),
                    "explanation": "Mudanca ou concentracao detectada automaticamente no recorte.",
                    "evidence": item.get("evidence", []),
                    "confidence": item.get("confidence", 0.6),
                }
            )
    for item in discovery.get("executive_surprises", []):
        changes.append(
            {
                "title": item.get("text"),
                "explanation": "Descoberta estatistica com suporte no recorte.",
                "evidence": item.get("evidence", []),
                "confidence": item.get("confidence", 0.6),
            }
        )
    if not changes:
        volume = analytical_enrichment.get("metrics_pack", {}).get("volume", {})
        total = volume.get("total_cards", 0)
        if total:
            changes.append(
                {
                    "title": "Sem mudanca dominante detectada",
                    "explanation": "O recorte tem dados suficientes para baseline, mas sem mudanca forte.",
                    "evidence": [f"total_cards={total}"],
                    "confidence": 0.55,
                }
            )
    return changes[:5]


def _headline(drivers: list[dict[str, Any]], discovery: dict[str, Any], risks: dict[str, Any]) -> str:
    if drivers:
        return f"A historia operacional do periodo foi dominada por {drivers[0]['title']}."
    if risks.get("high_risk_cards"):
        return "A historia operacional do periodo foi dominada por riscos concentrados."
    highlights = discovery.get("executive_highlights", [])
    if highlights:
        return f"A historia operacional do periodo foi marcada por {highlights[0].get('title')}."
    return "Nao ha evidencias suficientes para uma historia executiva conclusiva."


def _period_story(
    summary: dict[str, Any],
    metrics: dict[str, Any],
    headline: str,
    changes: list[dict[str, Any]],
    drivers: list[dict[str, Any]],
) -> str:
    total = metrics.get("volume", {}).get("total_cards") or summary.get("total_cards") or 0
    main_change = changes[0]["title"] if changes else "sem mudanca dominante"
    main_driver = drivers[0]["title"] if drivers else "sem driver dominante"
    return (
        f"{headline} O periodo analisou {total} cards; a principal mudanca foi {main_change}, "
        f"e o fator que mais explica o resultado foi {main_driver}."
    )


def _story_quality(
    *,
    headline: str,
    period_story: str,
    drivers: list[dict[str, Any]],
    root_causes: list[dict[str, Any]],
    business_implications: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    action_plan: list[dict[str, Any]],
    evidence_map: list[dict[str, Any]],
) -> dict[str, Any]:
    clarity = 20 if headline and period_story else 0
    evidence = min(20, len(evidence_map) * 2)
    prioritization = 20 if 1 <= len(drivers) <= 3 else 0
    cause_impact = 15 if root_causes and business_implications else 0
    actionable = 15 if decisions and action_plan else 0
    no_excess = 10 if len(drivers) <= 3 and len(decisions) <= 3 and len(action_plan) <= 7 else 0
    score = round(min(100, clarity + evidence + prioritization + cause_impact + actionable + no_excess), 1)
    return {
        "score": score,
        "label": "excelente" if score >= 85 else "bom" if score >= 70 else "regular" if score >= 50 else "baixo",
        "confidence": round(min(0.95, 0.45 + score / 200 + min(len(evidence_map), 20) / 100), 2),
        "criteria": {
            "clareza": clarity,
            "evidencia": evidence,
            "priorizacao": prioritization,
            "conexao_causa_impacto": cause_impact,
            "decisoes_acionaveis": actionable,
            "ausencia_excesso_informacao": no_excess,
        },
        "justification": [
            f"{len(drivers)} drivers priorizados",
            f"{len(decisions)} decisoes prontas para gestao",
            f"{len(evidence_map)} evidencias mapeadas",
        ],
    }


def _section(title: str, summary: str, evidence_items: list[Any]) -> dict[str, Any]:
    return {
        "title": title,
        "summary": summary or "Sem evidencias suficientes para esta secao.",
        "evidence": _normalize_evidence(evidence_items),
    }


def _risk_if_no_change(risks: dict[str, Any], discovery: dict[str, Any]) -> str:
    forecasts = discovery.get("what_happens_next", [])
    if forecasts:
        return forecasts[0].get("scenario", "")
    high = risks.get("high_risk_cards", [])
    if high:
        return f"{len(high)} cards de alto risco podem continuar pressionando prazo e execucao."
    return "Sem risco futuro dominante identificado com evidencia suficiente."


def _risk_evidence(risks: dict[str, Any], discovery: dict[str, Any]) -> list[str]:
    if discovery.get("what_happens_next"):
        return discovery["what_happens_next"][0].get("basis", [])
    return [item.get("card_id") for item in risks.get("high_risk_cards", [])[:5]]


def _evidence_entries(source: str, claim: str | None, values: list[Any]) -> list[dict[str, Any]]:
    return [
        {"source": source, "claim": claim or source, "evidence": str(value)}
        for value in values
        if str(value)
    ]


def _dedupe_evidence(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for item in items:
        key = (item.get("source"), item.get("claim"), item.get("evidence"))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result[:40]


def _normalize_evidence(items: list[Any]) -> list[str]:
    result = []
    for item in items:
        if isinstance(item, dict):
            value = item.get("evidence") or item.get("reason") or item.get("title") or item.get("decision")
            if isinstance(value, list):
                result.extend(str(v) for v in value if str(v))
            elif value:
                result.append(str(value))
        elif isinstance(item, list):
            result.extend(str(v) for v in item if str(v))
        elif item:
            result.append(str(item))
    return result[:8]


def _evidence_from_items(items: list[dict[str, Any]]) -> list[str]:
    evidence = []
    for item in items:
        evidence.extend(_normalize_evidence(item.get("evidence", [])))
    return evidence[:10]


def _join_titles(items: list[dict[str, Any]], *, key: str = "title") -> str:
    values = [str(item.get(key)) for item in items if item.get(key)]
    if not values:
        return "Sem evidencias suficientes."
    return "; ".join(values[:3])


def _driver_explanation(item: dict[str, Any]) -> str:
    return f"{item.get('title')} aparece entre os pontos de maior impacto do relatorio."


def _action_from_highlight(item: dict[str, Any]) -> str:
    kind = item.get("kind")
    if kind == "opportunity":
        return "Converter oportunidade em melhoria operacional priorizada."
    if kind == "correlation":
        return "Validar a correlacao e atacar o fator associado ao risco."
    return "Tratar o ponto com revisao gerencial e dono definido."


def _public_driver(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": item.get("title"),
        "explanation": item.get("explanation"),
        "evidence": item.get("evidence", []),
        "impact": item.get("impact", 0),
        "recommended_action": item.get("recommended_action"),
        "confidence": item.get("confidence", 0),
    }


def _consequence(urgency: str | None) -> str:
    if urgency == "alta":
        return "A exposicao operacional pode crescer ainda no ciclo atual."
    if urgency == "media":
        return "A tendencia pode persistir e consumir capacidade da equipe."
    return "A organizacao perde oportunidade de melhoria incremental."


def _severity_weight(severity: str | None) -> int:
    return {"critica": 4, "alta": 3, "media": 2, "baixa": 1}.get((severity or "").lower(), 0)


def _dedupe_by_title(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for item in items:
        title = item.get("title")
        if not title or title in seen:
            continue
        seen.add(title)
        result.append(item)
    return result


def _dedupe_decisions(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for item in items:
        key = item.get("decision")
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _dedupe_actions(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for item in items:
        key = item.get("action")
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
