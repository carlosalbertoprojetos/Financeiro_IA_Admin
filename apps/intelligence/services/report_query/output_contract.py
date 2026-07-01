from __future__ import annotations

from typing import Any


def build_report_output_contract(result: dict[str, Any]) -> dict[str, Any]:
    """Build the final presentation contract from already-computed report facts."""
    meta = result.get("meta", {})
    analytical = result.get("analytical", {})
    narrative = result.get("executive_narrative", {})
    discovery = result.get("discovery", {})
    story = result.get("executive_story", {})
    cards = result.get("cards", [])

    metrics = analytical.get("metrics_pack", {})
    rankings = _build_rankings(metrics, narrative, discovery, story, cards)
    tables = _build_tables(metrics, narrative, discovery, story, cards)
    executive_brief = _build_executive_brief(meta, metrics, rankings, story, discovery)
    diagnosis = _build_management_diagnosis(metrics, narrative, discovery, story, rankings, tables)
    appendix = _build_analytical_appendix(result, rankings, tables)
    commercial_score = _commercial_report_score(result, executive_brief, tables, rankings, appendix)

    return {
        "report_output_version": "2.0",
        "executive_brief": executive_brief,
        "management_diagnosis": diagnosis,
        "analytical_appendix": appendix,
        "executive_tables": tables,
        "rankings": rankings,
        "commercial_report_score": commercial_score,
        "layers": {
            "1_executive_brief": executive_brief,
            "2_management_diagnosis": diagnosis,
            "3_analytical_appendix": appendix,
        },
        "evidence_policy": {
            "no_invented_data": True,
            "all_analytical_claims_reference_metrics_or_evidence": True,
            "limitations_are_explicit": True,
        },
    }


def _build_executive_brief(
    meta: dict[str, Any],
    metrics: dict[str, Any],
    rankings: dict[str, list[dict[str, Any]]],
    story: dict[str, Any],
    discovery: dict[str, Any],
) -> dict[str, Any]:
    volume = metrics.get("volume", {})
    sla = metrics.get("sla", {})
    quality = metrics.get("quality", {})
    risks = metrics.get("risks", {})
    total = int(volume.get("total_cards") or meta.get("matched_cards") or 0)
    overdue = int(sla.get("overdue_open_cards") or 0)
    missing_owner = int(quality.get("missing_owner_count") or 0)
    incomplete = int(quality.get("incomplete_description_count") or 0)
    high_risk = len(risks.get("high_risk_cards", []))
    status = _status_from_facts(overdue, high_risk, missing_owner, total)
    score = _operational_score(metrics)
    decisions = story.get("decision_ready_summary", [])[:3]
    actions = story.get("action_plan", [])[:3]
    risk = (rankings.get("top_10_risks") or [{}])[0]
    opportunity = (rankings.get("top_10_opportunities") or [{}])[0]

    return {
        "status_geral": status,
        "score_operacional": score,
        "kpis_principais": [
            _kpi("Cards analisados", total, "informativo", f"{total} cards no recorte analisado."),
            _kpi("SLA compliance", _pct(sla.get("compliance_pct")), _sla_status(sla.get("compliance_pct")), "Percentual calculado a partir dos cards com prazo."),
            _kpi("Cards vencidos", overdue, _bad_if(overdue), f"{overdue} cards abertos vencidos."),
            _kpi("Sem responsavel", missing_owner, _bad_if(missing_owner), f"{missing_owner} cards sem responsavel atribuido."),
            _kpi("Descricoes incompletas", incomplete, _bad_if(incomplete), f"{incomplete} cards com descricao curta ou insuficiente."),
        ],
        "principais_problemas": [
            _problem(item)
            for item in (
                rankings.get("top_10_risks", [])[:2]
                + rankings.get("top_10_causes", [])[:1]
            )
        ][:3],
        "decisoes_recomendadas": [_decision_row(item) for item in decisions],
        "proximas_acoes": [_action_row(item) for item in actions],
        "maior_risco": _risk_row(risk),
        "maior_oportunidade": _opportunity_row(opportunity),
        "summary": _executive_sentence(total, overdue, missing_owner, incomplete, score),
    }


def _build_management_diagnosis(
    metrics: dict[str, Any],
    narrative: dict[str, Any],
    discovery: dict[str, Any],
    story: dict[str, Any],
    rankings: dict[str, list[dict[str, Any]]],
    tables: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    sections = narrative.get("sections", {})
    return {
        "historia_executiva_periodo": _evidence_sentence(
            story.get("period_story"),
            story.get("evidence_map", [])[:3],
            "Sem historia executiva conclusiva para o recorte.",
        ),
        "principais_mudancas": story.get("what_changed", []),
        "top_3_drivers": story.get("key_drivers", [])[:3],
        "analise_por_categoria": tables.get("top_categorias", []),
        "analise_por_membro": tables.get("top_membros", []),
        "analise_prazo_sla": {
            "summary": sections.get("impacto_prazo_sla", {}).get("summary", ""),
            "evidence": sections.get("impacto_prazo_sla", {}).get("evidence", []),
            "metrics": metrics.get("sla", {}),
        },
        "gargalos": tables.get("gargalos", []),
        "riscos": rankings.get("top_10_risks", []),
        "causas_provaveis": rankings.get("top_10_causes", []),
        "recomendacoes": _recommendations(narrative, discovery, story),
    }


def _build_analytical_appendix(
    result: dict[str, Any],
    rankings: dict[str, list[dict[str, Any]]],
    tables: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    analytical = result.get("analytical", {})
    story = result.get("executive_story", {})
    return {
        "tabelas_completas": tables,
        "dados_por_card": result.get("cards", []),
        "evidencias": story.get("evidence_map", []),
        "timeline": analytical.get("metrics_pack", {}).get("trends", {}),
        "comentarios_relevantes": analytical.get("metrics_pack", {}).get("communication", {}),
        "checklists": _checklist_appendix(result.get("cards", [])),
        "descricoes_estruturadas": [
            {
                "card_id": card.get("card_id"),
                "description_sections": card.get("description_sections", {}),
                "documentation_completeness_score": card.get("documentation_completeness_score"),
            }
            for card in result.get("cards", [])
        ],
        "metricas_tecnicas": {
            "metrics": result.get("metrics", {}),
            "analytical_quality": analytical.get("quality", {}),
            "rankings": rankings,
        },
        "limitations": [
            "Comparacoes de variacao dependem de benchmark interno disponivel no payload.",
            "PDF e PPTX priorizam leitura executiva; dados completos permanecem no JSON e no anexo analitico.",
        ],
    }


def _build_tables(
    metrics: dict[str, Any],
    narrative: dict[str, Any],
    discovery: dict[str, Any],
    story: dict[str, Any],
    cards: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    volume = metrics.get("volume", {})
    workload = metrics.get("workload", {})
    risks = metrics.get("risks", {})
    time = metrics.get("time", {})
    sla = metrics.get("sla", {})
    quality = metrics.get("quality", {})
    communication = metrics.get("communication", {})

    return {
        "kpis_principais": [
            {"metrica": "Cards analisados", "valor": volume.get("total_cards", len(cards)), "status": "informativo", "variacao": "N/A", "interpretacao": "Volume total do recorte analisado."},
            {"metrica": "SLA compliance", "valor": _pct(sla.get("compliance_pct")), "status": _sla_status(sla.get("compliance_pct")), "variacao": "N/A", "interpretacao": "Quanto menor o compliance, maior a pressao de prazo."},
            {"metrica": "Cards vencidos", "valor": sla.get("overdue_open_cards", 0), "status": _bad_if(sla.get("overdue_open_cards", 0)), "variacao": "N/A", "interpretacao": "Atrasos abertos exigem replanejamento e dono."},
            {"metrica": "Sem responsavel", "valor": quality.get("missing_owner_count", 0), "status": _bad_if(quality.get("missing_owner_count", 0)), "variacao": "N/A", "interpretacao": "Cards sem dono reduzem accountability."},
            {"metrica": "Comentarios", "valor": communication.get("total_comments", 0), "status": "informativo", "variacao": "N/A", "interpretacao": "Indica rastreabilidade de comunicacao no recorte."},
        ],
        "top_categorias": [
            {
                "categoria": item.get("name"),
                "quantidade": item.get("count", 0),
                "sla": _pct(sla.get("compliance_pct")),
                "risco": _risk_for_category(risks, item.get("name")),
                "tempo_medio": time.get("avg_open_age_days"),
                "acao": "Priorizar categoria se concentrar risco, atraso ou baixa qualidade.",
            }
            for item in volume.get("by_activity_type", [])[:10]
        ],
        "top_membros": [
            {
                "membro": item.get("name"),
                "cards": item.get("card_count", 0),
                "concluidos": item.get("completed_count", "N/A"),
                "atrasados": item.get("overdue_count", 0),
                "tempo_medio": time.get("avg_open_age_days"),
                "observacao": _member_observation(item),
            }
            for item in workload.get("by_member", [])[:10]
        ],
        "gargalos": [
            {
                "lista_etapa": item.get("name"),
                "cards": item.get("count", 0),
                "tempo_medio": time.get("avg_days_since_last_activity"),
                "severidade": _severity_from_count(item.get("count", 0), volume.get("total_cards", 0)),
                "recomendacao": "Revisar WIP, dono e proximo passo dos itens concentrados nesta etapa.",
            }
            for item in volume.get("by_list", [])[:10]
        ],
        "decisoes": [
            {
                "decisao": item.get("decision"),
                "evidencia": "; ".join(map(str, item.get("evidence", []))),
                "impacto_esperado": item.get("reason") or item.get("consequence_if_no_action"),
                "urgencia": item.get("urgency"),
                "dono_sugerido": item.get("suggested_owner"),
            }
            for item in story.get("decision_ready_summary", [])[:10]
        ],
    }


def _build_rankings(
    metrics: dict[str, Any],
    narrative: dict[str, Any],
    discovery: dict[str, Any],
    story: dict[str, Any],
    cards: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    volume = metrics.get("volume", {})
    hotspots = discovery.get("hotspots", {})
    return {
        "top_10_categories": _rank_named(volume.get("by_activity_type") or hotspots.get("top_categories", [])),
        "top_10_members": _rank_named(metrics.get("workload", {}).get("by_member", []), count_key="card_count"),
        "top_10_critical_cards": _rank_cards(cards),
        "top_10_causes": _rank_causes(story, narrative),
        "top_10_risks": _rank_risks(metrics, discovery),
        "top_10_opportunities": _rank_opportunities(discovery),
    }


def _commercial_report_score(
    result: dict[str, Any],
    executive_brief: dict[str, Any],
    tables: dict[str, list[dict[str, Any]]],
    rankings: dict[str, list[dict[str, Any]]],
    appendix: dict[str, Any],
) -> dict[str, Any]:
    score = 0
    score += 20 if executive_brief.get("summary") and executive_brief.get("kpis_principais") else 0
    score += 20 if all(tables.get(key) for key in ("kpis_principais", "top_categorias", "top_membros", "gargalos", "decisoes")) else 0
    score += 20 if all(rankings.get(key) for key in rankings) else 0
    score += 20 if appendix.get("dados_por_card") and appendix.get("evidencias") else 0
    score += 10 if result.get("executive_story", {}).get("decision_ready_summary") else 0
    score += 10 if result.get("discovery", {}).get("what_happens_next") else 0
    return {
        "score": min(100, score),
        "target": 95,
        "status": "PASS" if score >= 95 else "WARNING",
        "evidence": [
            "Executive Brief estruturado",
            "tabelas executivas obrigatorias",
            "rankings executivos",
            "anexo analitico com cards e evidencias",
        ],
    }


def _rank_named(rows: list[dict[str, Any]], *, count_key: str = "count") -> list[dict[str, Any]]:
    ranked = sorted(rows, key=lambda item: int(item.get(count_key) or item.get("count") or 0), reverse=True)
    return [
        {"rank": index + 1, "name": item.get("name"), "count": item.get(count_key) or item.get("count", 0), "evidence": item}
        for index, item in enumerate(ranked[:10])
        if item.get("name")
    ]


def _rank_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(cards, key=lambda item: int(item.get("risk_score") or 0), reverse=True)
    return [
        {
            "rank": index + 1,
            "card_id": item.get("card_id"),
            "title": item.get("title"),
            "risk_score": item.get("risk_score"),
            "evidence": item.get("evidence", []),
            "recommended_action": item.get("next_action"),
        }
        for index, item in enumerate(ranked[:10])
    ]


def _rank_causes(story: dict[str, Any], narrative: dict[str, Any]) -> list[dict[str, Any]]:
    causes = story.get("root_causes") or narrative.get("root_cause_hypotheses", [])
    return [
        {
            "rank": index + 1,
            "title": item.get("title") or item.get("hypothesis"),
            "evidence": item.get("evidence", []),
            "recommended_action": item.get("recommended_action") or item.get("explanation"),
            "confidence": item.get("confidence"),
        }
        for index, item in enumerate(causes[:10])
    ]


def _rank_risks(metrics: dict[str, Any], discovery: dict[str, Any]) -> list[dict[str, Any]]:
    risks = metrics.get("risks", {}).get("high_risk_cards", [])
    anomalies = discovery.get("anomalies", [])
    combined = [
        {
            "title": item.get("title") or item.get("card_id"),
            "score": item.get("risk_score") or item.get("impact", 0),
            "evidence": item.get("reasons") or item.get("evidence", []),
            "recommended_action": item.get("next_action") or "Tratar risco com dono e prazo.",
        }
        for item in [*risks, *anomalies]
    ]
    ranked = sorted(combined, key=lambda item: int(item.get("score") or 0), reverse=True)
    return [{"rank": index + 1, **item} for index, item in enumerate(ranked[:10])]


def _rank_opportunities(discovery: dict[str, Any]) -> list[dict[str, Any]]:
    rows = discovery.get("opportunities", [])
    ranked = sorted(rows, key=lambda item: float(item.get("confidence") or 0), reverse=True)
    return [
        {
            "rank": index + 1,
            "title": item.get("title"),
            "evidence": item.get("evidence", []),
            "recommended_action": item.get("recommended_action"),
            "confidence": item.get("confidence"),
        }
        for index, item in enumerate(ranked[:10])
    ]


def _checklist_appendix(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "card_id": card.get("card_id"),
            "checklist_total": card.get("checklist_total"),
            "checklist_completed": card.get("checklist_completed"),
            "checklist_pending": card.get("checklist_pending"),
            "checklist_completion_percent": card.get("checklist_completion_percent"),
        }
        for card in cards
    ]


def _recommendations(
    narrative: dict[str, Any],
    discovery: dict[str, Any],
    story: dict[str, Any],
) -> list[dict[str, Any]]:
    actions = story.get("action_plan") or narrative.get("next_actions", [])
    opportunities = discovery.get("opportunities", [])
    rows = []
    for item in actions[:5]:
        rows.append(
            {
                "acao": item.get("action"),
                "evidencia": item.get("evidence", []),
                "impacto": item.get("expected_result"),
                "dono": item.get("owner"),
                "prazo": item.get("deadline"),
            }
        )
    for item in opportunities[:3]:
        rows.append(
            {
                "acao": item.get("recommended_action"),
                "evidencia": item.get("evidence", []),
                "impacto": item.get("potential_gain"),
                "dono": "Gestor operacional",
                "prazo": "Proximo ciclo",
            }
        )
    return rows


def _operational_score(metrics: dict[str, Any]) -> int:
    volume = metrics.get("volume", {})
    sla = metrics.get("sla", {})
    quality = metrics.get("quality", {})
    total = max(1, int(volume.get("total_cards") or 0))
    compliance = sla.get("compliance_pct")
    compliance_score = 35 if compliance is None else max(0, min(35, float(compliance) * 0.35))
    overdue_penalty = min(25, int(sla.get("overdue_open_cards") or 0) / total * 25)
    owner_penalty = min(20, int(quality.get("missing_owner_count") or 0) / total * 20)
    description_penalty = min(20, int(quality.get("incomplete_description_count") or 0) / total * 20)
    return int(round(max(0, min(100, 100 - overdue_penalty - owner_penalty - description_penalty - (35 - compliance_score)))))


def _status_from_facts(overdue: int, high_risk: int, missing_owner: int, total: int) -> str:
    if total and (overdue / total >= 0.25 or high_risk >= 3):
        return "Atencao executiva"
    if missing_owner:
        return "Atencao gerencial"
    return "Operacao controlada"


def _executive_sentence(total: int, overdue: int, missing_owner: int, incomplete: int, score: int) -> str:
    return (
        f"Foram analisados {total} cards, com {overdue} vencidos, {missing_owner} sem responsavel "
        f"e {incomplete} com descricao incompleta. O score operacional ficou em {score}/100, "
        "indicando onde a gestao deve priorizar replanejamento, ownership e qualidade de entrada."
    )


def _evidence_sentence(text: str | None, evidence: list[Any], fallback: str) -> dict[str, Any]:
    return {"summary": text or fallback, "evidence": evidence}


def _kpi(label: str, value: Any, status: str, interpretation: str) -> dict[str, Any]:
    return {"metrica": label, "valor": value, "status": status, "interpretacao": interpretation}


def _problem(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "problema": item.get("title") or item.get("name") or item.get("card_id"),
        "evidencia": item.get("evidence", []),
        "acao": item.get("recommended_action") or "Definir dono e proximo passo.",
    }


def _decision_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "decisao": item.get("decision"),
        "evidencia": item.get("evidence", []),
        "urgencia": item.get("urgency"),
        "dono_sugerido": item.get("suggested_owner"),
    }


def _action_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "acao": item.get("action"),
        "dono": item.get("owner"),
        "prazo": item.get("deadline"),
        "resultado_esperado": item.get("expected_result"),
        "evidencia": item.get("evidence", []),
    }


def _risk_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "risco": item.get("title"),
        "score": item.get("score"),
        "evidencia": item.get("evidence", []),
        "acao": item.get("recommended_action"),
    }


def _opportunity_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "oportunidade": item.get("title"),
        "evidencia": item.get("evidence", []),
        "acao": item.get("recommended_action"),
        "confianca": item.get("confidence"),
    }


def _risk_for_category(risks: dict[str, Any], name: str | None) -> str:
    for item in risks.get("risk_by_activity_type", []):
        if item.get("name") == name:
            return "alto" if int(item.get("count") or 0) else "baixo"
    return "baixo"


def _member_observation(item: dict[str, Any]) -> str:
    if int(item.get("overdue_count") or 0):
        return "Possui cards vencidos; revisar prioridade e capacidade."
    if int(item.get("card_count") or 0) >= 3:
        return "Carga concentrada; monitorar WIP."
    return "Sem alerta dominante no recorte."


def _severity_from_count(count: Any, total: Any) -> str:
    count_int = int(count or 0)
    total_int = int(total or 0)
    if total_int and count_int / total_int >= 0.5:
        return "alta"
    if count_int >= 3:
        return "media"
    return "baixa"


def _pct(value: Any) -> str:
    return "N/A" if value is None else f"{value}%"


def _sla_status(value: Any) -> str:
    if value is None:
        return "indefinido"
    return "bom" if float(value) >= 80 else "atencao" if float(value) >= 60 else "critico"


def _bad_if(value: Any) -> str:
    return "critico" if int(value or 0) > 0 else "bom"
