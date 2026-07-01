from __future__ import annotations

from typing import Any


SEVERITY_WEIGHT = {
    "critica": 4,
    "alta": 3,
    "media": 2,
    "baixa": 1,
}


def build_executive_narrative(analytical: dict[str, Any]) -> dict[str, Any]:
    metrics = analytical.get("metrics_pack", {})
    recommendations = analytical.get("recommendations", [])
    card_analysis = analytical.get("activity_classification", {}).get("cards", [])
    insights = _prioritize_insights(metrics, recommendations, card_analysis)
    root_causes = _build_root_cause_hypotheses(metrics, card_analysis)
    management_decisions = _build_management_decisions(metrics, recommendations, root_causes)
    next_actions = _build_next_actions(insights, recommendations, card_analysis)
    sections = _build_sections(metrics, insights, root_causes, management_decisions, next_actions)
    readability = _score_readability(sections, insights, root_causes, management_decisions)

    return {
        "sections": sections,
        "insights": insights,
        "root_cause_hypotheses": root_causes,
        "management_decisions": management_decisions,
        "next_actions": next_actions,
        "executive_readability_score": readability,
        "evidence_policy": {
            "narrative_claims_require_metric_or_evidence": True,
            "deterministic_generation": True,
        },
    }


def _prioritize_insights(
    metrics: dict[str, Any],
    recommendations: list[dict[str, Any]],
    card_analysis: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    insights: list[dict[str, Any]] = []
    sla = metrics.get("sla", {})
    quality = metrics.get("quality", {})
    communication = metrics.get("communication", {})
    workload = metrics.get("workload", {})
    risks = metrics.get("risks", {})
    time = metrics.get("time", {})

    if risks.get("high_risk_cards"):
        top_cards = risks["high_risk_cards"][:3]
        insights.append(
            _insight(
                title="Cards criticos concentram o risco operacional",
                severity="alta",
                metric_source="metrics_pack.risks.high_risk_cards",
                evidence=[f"{item['card_id']} risco={item['risk_score']}" for item in top_cards],
                affected_area="Operacao",
                business_impact="A execucao pode perder previsibilidade se os itens criticos seguirem sem intervencao.",
                recommended_action=top_cards[0].get("next_action") or "Priorizar intervencao nos cards de maior risco.",
                confidence=_confidence_from_count(len(top_cards)),
                risk=4,
                impact=4,
                urgency=4,
                recurrence=len(top_cards),
            )
        )

    if sla.get("overdue_open_cards"):
        insights.append(
            _insight(
                title="Itens abertos vencidos pressionam o SLA",
                severity="alta",
                metric_source="metrics_pack.sla.overdue_open_cards",
                evidence=[f"{sla['overdue_open_cards']} cards abertos vencidos"],
                affected_area="Prazo/SLA",
                business_impact="O atraso aberto aumenta risco de descumprimento e replanejamento de entregas.",
                recommended_action="Replanejar cards vencidos e registrar nova data de compromisso.",
                confidence=0.9,
                risk=4,
                impact=4,
                urgency=4,
                recurrence=int(sla["overdue_open_cards"]),
            )
        )

    if quality.get("missing_owner_count"):
        insights.append(
            _insight(
                title="Cards sem responsavel reduzem accountability",
                severity="media",
                metric_source="metrics_pack.quality.missing_owner_count",
                evidence=[f"{quality['missing_owner_count']} cards sem responsavel"],
                affected_area="Triagem",
                business_impact="Sem dono claro, a gestao perde rastreabilidade de execucao e decisao.",
                recommended_action="Atribuir responsaveis antes de iniciar ou repriorizar novos cards.",
                confidence=0.85,
                risk=3,
                impact=3,
                urgency=3,
                recurrence=int(quality["missing_owner_count"]),
            )
        )

    if quality.get("incomplete_description_count"):
        insights.append(
            _insight(
                title="Descricoes incompletas limitam a leitura executiva",
                severity="media",
                metric_source="metrics_pack.quality.incomplete_description_count",
                evidence=[f"{quality['incomplete_description_count']} descricoes incompletas"],
                affected_area="Qualidade de especificacao",
                business_impact="A baixa qualidade de contexto aumenta retrabalho e decisao por suposicao.",
                recommended_action="Exigir descricao minima com objetivo, criterio, risco e proximo passo.",
                confidence=0.8,
                risk=2,
                impact=3,
                urgency=2,
                recurrence=int(quality["incomplete_description_count"]),
            )
        )

    if communication.get("cards_without_comments"):
        insights.append(
            _insight(
                title="Parte dos cards nao tem trilha de comunicacao",
                severity="baixa",
                metric_source="metrics_pack.communication.cards_without_comments",
                evidence=[f"{communication['cards_without_comments']} cards sem comentarios"],
                affected_area="Comunicacao",
                business_impact="Decisoes e bloqueios podem ficar fora do sistema, reduzindo auditabilidade.",
                recommended_action="Registrar decisao ou proximo passo nos cards sem comentario relevante.",
                confidence=0.7,
                risk=2,
                impact=2,
                urgency=2,
                recurrence=int(communication["cards_without_comments"]),
            )
        )

    overloaded = [
        item
        for item in workload.get("by_member", [])
        if item.get("card_count", 0) >= 3 or item.get("overdue_count", 0) > 0
    ]
    if overloaded:
        top = overloaded[0]
        insights.append(
            _insight(
                title="Carga concentrada exige revisao gerencial",
                severity="media",
                metric_source="metrics_pack.workload.by_member",
                evidence=[f"{top['name']}: {top['card_count']} cards, {top['overdue_count']} vencidos"],
                affected_area="Capacidade",
                business_impact="Concentracao de carga aumenta fila, atraso e dependencia de uma pessoa.",
                recommended_action="Redistribuir cards ou explicitar prioridade dos itens do responsavel mais carregado.",
                confidence=0.75,
                risk=3,
                impact=3,
                urgency=3,
                recurrence=int(top["card_count"]),
            )
        )

    if time.get("stale_cards_7d"):
        insights.append(
            _insight(
                title="Cards parados indicam possivel gargalo de decisao",
                severity="media",
                metric_source="metrics_pack.time.stale_cards_7d",
                evidence=[f"{time['stale_cards_7d']} cards sem atividade ha 7 dias ou mais"],
                affected_area="Fluxo",
                business_impact="Itens parados consomem WIP e atrasam a entrega de valor.",
                recommended_action="Revisar cards parados e registrar desbloqueio, descarte ou nova prioridade.",
                confidence=0.78,
                risk=3,
                impact=3,
                urgency=3,
                recurrence=int(time["stale_cards_7d"]),
            )
        )

    for recommendation in recommendations:
        evidence = [str(item) for item in recommendation.get("evidence", []) if str(item)]
        if not evidence:
            continue
        insights.append(
            _insight(
                title=recommendation.get("reason") or "Recomendacao operacional com evidencia",
                severity=_severity_from_priority(recommendation.get("priority")),
                metric_source="analytical.recommendations",
                evidence=evidence,
                affected_area="Gestao operacional",
                business_impact=recommendation.get("reason") or "A recomendacao reduz risco operacional identificado.",
                recommended_action=recommendation.get("action") or "Executar recomendacao registrada.",
                confidence=0.72,
                risk=SEVERITY_WEIGHT.get(_severity_from_priority(recommendation.get("priority")), 1),
                impact=3,
                urgency=SEVERITY_WEIGHT.get(_severity_from_priority(recommendation.get("priority")), 1),
                recurrence=len(evidence),
            )
        )

    if not insights:
        total_cards = metrics.get("volume", {}).get("total_cards", 0)
        insights.append(
            _insight(
                title="Nao ha evidencias suficientes para achados criticos",
                severity="baixa",
                metric_source="metrics_pack.volume.total_cards",
                evidence=[f"{total_cards} cards analisados"],
                affected_area="Relatorio",
                business_impact="A decisao deve focar em melhorar dados antes de tirar conclusoes fortes.",
                recommended_action="Completar dados operacionais e gerar novo relatorio.",
                confidence=0.6,
                risk=1,
                impact=1,
                urgency=1,
                recurrence=1,
            )
        )

    unique = _dedupe_insights(insights)
    return sorted(
        unique,
        key=lambda item: (
            item["_rank"]["risk"],
            item["_rank"]["impact"],
            item["_rank"]["urgency"],
            item["_rank"]["recurrence"],
        ),
        reverse=True,
    )


def _build_root_cause_hypotheses(metrics: dict[str, Any], card_analysis: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hypotheses: list[dict[str, Any]] = []
    sla = metrics.get("sla", {})
    quality = metrics.get("quality", {})
    communication = metrics.get("communication", {})
    time = metrics.get("time", {})
    risks = metrics.get("risks", {})

    if sla.get("overdue_open_cards") and time.get("stale_cards_7d"):
        hypotheses.append(
            _hypothesis(
                hypothesis="Atrasos podem estar ligados a cards parados sem decisao recente.",
                evidence=[
                    f"{sla['overdue_open_cards']} cards abertos vencidos",
                    f"{time['stale_cards_7d']} cards sem atividade ha 7 dias ou mais",
                ],
                confidence=0.82,
                how_to_validate="Revisar os cards vencidos e confirmar se existe bloqueio, aguardando validacao ou falta de prioridade.",
                recommended_action="Criar revisao diaria dos vencidos ate reduzir o estoque critico.",
            )
        )

    if quality.get("missing_owner_count"):
        hypotheses.append(
            _hypothesis(
                hypothesis="A triagem pode estar falhando ao permitir cards sem dono claro.",
                evidence=[f"{quality['missing_owner_count']} cards sem responsavel"],
                confidence=0.85,
                how_to_validate="Checar se os cards sem responsavel estao em backlog, entrada ou etapas de execucao.",
                recommended_action="Bloquear entrada em execucao sem responsavel definido.",
            )
        )

    if quality.get("incomplete_description_count") and quality.get("cards_with_pending_checklists"):
        hypotheses.append(
            _hypothesis(
                hypothesis="Baixa qualidade de especificacao pode estar gerando pendencias operacionais.",
                evidence=[
                    f"{quality['incomplete_description_count']} descricoes incompletas",
                    f"{quality['cards_with_pending_checklists']} cards com checklist pendente",
                ],
                confidence=0.74,
                how_to_validate="Comparar cards com descricao curta contra pendencias, retrabalho ou comentarios de duvida.",
                recommended_action="Adotar criterio minimo de descricao antes da triagem.",
            )
        )

    if communication.get("total_comments") and not communication.get("cards_with_decision_evidence"):
        hypotheses.append(
            _hypothesis(
                hypothesis="A comunicacao pode estar acontecendo sem registrar conclusao executavel.",
                evidence=[
                    f"{communication['total_comments']} comentarios registrados",
                    "0 cards com evidencia explicita de decisao",
                ],
                confidence=0.68,
                how_to_validate="Amostre comentarios recentes e verifique se terminam com dono, prazo e decisao.",
                recommended_action="Padronizar comentarios de decisao com acao, dono e prazo.",
            )
        )

    if risks.get("risk_by_activity_type"):
        top = risks["risk_by_activity_type"][0]
        hypotheses.append(
            _hypothesis(
                hypothesis=f"Risco concentrado em {top['name']} pode indicar gargalo especializado.",
                evidence=[f"{top['count']} cards de alto risco em {top['name']}"],
                confidence=0.7,
                how_to_validate="Verificar se os cards dessa categoria dependem das mesmas pessoas, etapas ou validacoes.",
                recommended_action="Tratar a categoria de maior risco como frente prioritaria de gestao.",
            )
        )

    if not hypotheses:
        total_cards = metrics.get("volume", {}).get("total_cards", 0)
        hypotheses.append(
            _hypothesis(
                hypothesis="Nao ha padrao causal forte no recorte analisado.",
                evidence=[f"{total_cards} cards analisados"],
                confidence=0.55,
                how_to_validate="Aumentar o periodo ou melhorar o preenchimento dos cards para confirmar padroes.",
                recommended_action="Usar o relatorio como baseline e comparar com a proxima execucao.",
            )
        )
    return hypotheses


def _build_management_decisions(
    metrics: dict[str, Any],
    recommendations: list[dict[str, Any]],
    root_causes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    sla = metrics.get("sla", {})
    quality = metrics.get("quality", {})
    workload = metrics.get("workload", {})
    risks = metrics.get("risks", {})

    if risks.get("high_risk_cards"):
        decisions.append(
            _decision(
                decision="Repriorizar cards criticos no proximo ciclo de gestao.",
                reason=f"{len(risks['high_risk_cards'])} cards aparecem como alto risco.",
                expected_impact="Reduzir exposicao operacional e aumentar previsibilidade do fluxo.",
                urgency="alta",
                suggested_owner="Gestor operacional",
                suggested_deadline="Hoje",
            )
        )

    if workload.get("by_member"):
        top = workload["by_member"][0]
        if top.get("card_count", 0) >= 3 or top.get("overdue_count", 0):
            decisions.append(
                _decision(
                    decision="Redistribuir carga ou explicitar prioridade do responsavel mais carregado.",
                    reason=f"{top['name']} concentra {top['card_count']} cards e {top['overdue_count']} vencidos.",
                    expected_impact="Diminuir fila individual e dependencia operacional.",
                    urgency="media",
                    suggested_owner="Lider da equipe",
                    suggested_deadline="24h",
                )
            )

    if sla.get("cards_without_due_date"):
        decisions.append(
            _decision(
                decision="Definir SLA ou data alvo para cards sem prazo.",
                reason=f"{sla['cards_without_due_date']} cards nao possuem data de vencimento.",
                expected_impact="Melhorar previsibilidade e priorizacao.",
                urgency="media",
                suggested_owner="Gestor operacional",
                suggested_deadline="48h",
            )
        )

    if quality.get("incomplete_description_count"):
        decisions.append(
            _decision(
                decision="Exigir descricao minima para novos cards.",
                reason=f"{quality['incomplete_description_count']} cards possuem descricao incompleta.",
                expected_impact="Reduzir ambiguidades, retrabalho e decisao por suposicao.",
                urgency="media",
                suggested_owner="PMO ou lider da operacao",
                suggested_deadline="7 dias",
            )
        )

    if recommendations and not decisions:
        first = recommendations[0]
        decisions.append(
            _decision(
                decision=first.get("action", "Executar recomendacao prioritaria."),
                reason=first.get("reason", "Ha recomendacao operacional com evidencia."),
                expected_impact="Melhorar controle operacional do recorte analisado.",
                urgency=first.get("priority", "media"),
                suggested_owner="Gestor operacional",
                suggested_deadline="Proximo ciclo",
            )
        )

    if not decisions:
        first_cause = root_causes[0]
        decisions.append(
            _decision(
                decision="Aumentar qualidade dos dados antes de tomar decisao estrutural.",
                reason=first_cause["hypothesis"],
                expected_impact="Evitar conclusoes fortes sem evidencias suficientes.",
                urgency="baixa",
                suggested_owner="Gestor operacional",
                suggested_deadline="7 dias",
            )
        )
    return decisions


def _build_next_actions(
    insights: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
    card_analysis: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for insight in insights[:5]:
        actions.append(
            {
                "action": insight["recommended_action"],
                "source": insight["metric_source"],
                "evidence": insight["evidence"],
                "urgency": insight["severity"],
            }
        )
    for recommendation in recommendations[:3]:
        evidence = [str(item) for item in recommendation.get("evidence", []) if str(item)]
        if evidence:
            actions.append(
                {
                    "action": recommendation.get("action"),
                    "source": "analytical.recommendations",
                    "evidence": evidence,
                    "urgency": recommendation.get("priority", "media"),
                }
            )
    for card in card_analysis:
        evidence = card.get("evidence") or []
        if card.get("next_action") and evidence:
            actions.append(
                {
                    "action": card["next_action"],
                    "source": f"card:{card['card_id']}",
                    "evidence": [item.get("evidence", "") for item in evidence[:3]],
                    "urgency": "alta" if card.get("risk_score", 0) >= 60 else "media",
                }
            )
        if len(actions) >= 9:
            break
    return _dedupe_actions(actions)[:9]


def _build_sections(
    metrics: dict[str, Any],
    insights: list[dict[str, Any]],
    root_causes: list[dict[str, Any]],
    management_decisions: list[dict[str, Any]],
    next_actions: list[dict[str, Any]],
) -> dict[str, Any]:
    sla = metrics.get("sla", {})
    quality = metrics.get("quality", {})
    risks = metrics.get("risks", {})
    volume = metrics.get("volume", {})
    time = metrics.get("time", {})
    top_insight = insights[0]
    top_cause = root_causes[0]
    top_decision = management_decisions[0]

    return {
        "diagnostico_executivo": _section(
            "Diagnostico Executivo",
            (
                f"O recorte analisado contem {volume.get('total_cards', 0)} cards. "
                f"O principal achado e: {top_insight['title']}."
            ),
            [f"metrics_pack.volume.total_cards={volume.get('total_cards', 0)}", *top_insight["evidence"]],
        ),
        "principais_achados": _section(
            "Principais Achados",
            "Os achados priorizados indicam onde a gestao deve concentrar atencao primeiro.",
            [item["title"] for item in insights[:5]],
        ),
        "causas_provaveis": _section(
            "Causas Provaveis",
            top_cause["hypothesis"],
            top_cause["evidence"],
        ),
        "impacto_operacional": _section(
            "Impacto Operacional",
            top_insight["business_impact"],
            top_insight["evidence"],
        ),
        "impacto_prazo_sla": _section(
            "Impacto em Prazo/SLA",
            (
                f"SLA atual: {sla.get('compliance_pct', 'N/A')}% de compliance, "
                f"{sla.get('overdue_open_cards', 0)} cards abertos vencidos e "
                f"{sla.get('cards_due_in_48h', 0)} com vencimento em ate 48h."
            ),
            [
                f"compliance_pct={sla.get('compliance_pct', 'N/A')}",
                f"overdue_open_cards={sla.get('overdue_open_cards', 0)}",
                f"cards_due_in_48h={sla.get('cards_due_in_48h', 0)}",
            ],
        ),
        "riscos_prioritarios": _section(
            "Riscos Prioritarios",
            (
                f"Foram identificados {len(risks.get('high_risk_cards', []))} cards de alto risco "
                f"e {time.get('stale_cards_7d', 0)} cards parados ha 7 dias ou mais."
            ),
            [
                f"high_risk_cards={len(risks.get('high_risk_cards', []))}",
                f"stale_cards_7d={time.get('stale_cards_7d', 0)}",
            ],
        ),
        "recomendacoes_acionaveis": _section(
            "Recomendacoes Acionaveis",
            top_insight["recommended_action"],
            top_insight["evidence"],
        ),
        "decisoes_necessarias_gestao": _section(
            "Decisoes Necessarias da Gestao",
            top_decision["decision"],
            [top_decision["reason"]],
        ),
        "proximas_acoes": _section(
            "Proximas Acoes",
            next_actions[0]["action"],
            next_actions[0]["evidence"],
        ),
        "readability_inputs": {
            "quality_evidence": [
                f"incomplete_description_count={quality.get('incomplete_description_count', 0)}",
                f"missing_owner_count={quality.get('missing_owner_count', 0)}",
            ]
        },
    }


def _score_readability(
    sections: dict[str, Any],
    insights: list[dict[str, Any]],
    root_causes: list[dict[str, Any]],
    management_decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    narrative_sections = [value for key, value in sections.items() if key != "readability_inputs"]
    non_empty = sum(1 for section in narrative_sections if section.get("summary") and section.get("evidence"))
    clarity = non_empty / len(narrative_sections) * 25 if narrative_sections else 0
    recommendations = 20 if any(item.get("recommended_action") for item in insights) else 0
    decisions = 20 if management_decisions else 0
    metric_link = 20 if all(item.get("metric_source") and item.get("evidence") for item in insights) else 0
    language = 15 if root_causes and all(item.get("how_to_validate") for item in root_causes) else 8
    score = round(min(100, clarity + recommendations + decisions + metric_link + language), 1)
    return {
        "score": score,
        "label": "excelente" if score >= 85 else "bom" if score >= 70 else "regular" if score >= 50 else "baixo",
        "criteria": {
            "clareza_diagnostico": round(clarity, 1),
            "recomendacoes_presentes": recommendations,
            "decisao_sugerida": decisions,
            "metrica_ligada_a_conclusao": metric_link,
            "linguagem_executiva": language,
        },
        "justification": [
            f"{non_empty} de {len(narrative_sections)} secoes narrativas possuem resumo e evidencia",
            f"{len(insights)} insights priorizados com origem metrica",
            f"{len(management_decisions)} decisoes de gestao sugeridas",
        ],
    }


def _insight(
    *,
    title: str,
    severity: str,
    metric_source: str,
    evidence: list[str],
    affected_area: str,
    business_impact: str,
    recommended_action: str,
    confidence: float,
    risk: int,
    impact: int,
    urgency: int,
    recurrence: int,
) -> dict[str, Any]:
    return {
        "title": title,
        "severity": severity,
        "metric_source": metric_source,
        "evidence": evidence,
        "affected_area": affected_area,
        "business_impact": business_impact,
        "recommended_action": recommended_action,
        "confidence": round(confidence, 2),
        "_rank": {
            "risk": risk,
            "impact": impact,
            "urgency": urgency,
            "recurrence": recurrence,
        },
    }


def _hypothesis(
    *,
    hypothesis: str,
    evidence: list[str],
    confidence: float,
    how_to_validate: str,
    recommended_action: str,
) -> dict[str, Any]:
    return {
        "hypothesis": hypothesis,
        "evidence": evidence,
        "confidence": round(confidence, 2),
        "how_to_validate": how_to_validate,
        "recommended_action": recommended_action,
    }


def _decision(
    *,
    decision: str,
    reason: str,
    expected_impact: str,
    urgency: str,
    suggested_owner: str,
    suggested_deadline: str,
) -> dict[str, Any]:
    return {
        "decision": decision,
        "reason": reason,
        "expected_impact": expected_impact,
        "urgency": urgency,
        "suggested_owner": suggested_owner,
        "suggested_deadline": suggested_deadline,
    }


def _section(title: str, summary: str, evidence: list[str]) -> dict[str, Any]:
    clean_evidence = [str(item) for item in evidence if str(item)]
    if not clean_evidence:
        clean_evidence = ["Sem evidencia suficiente no recorte analisado"]
    return {
        "title": title,
        "summary": summary or "Sem dados suficientes para conclusao executiva.",
        "evidence": clean_evidence,
    }


def _severity_from_priority(priority: str | None) -> str:
    value = (priority or "").lower()
    if value in {"critica", "critico", "alta"}:
        return "alta"
    if value in {"media", "moderada"}:
        return "media"
    return "baixa"


def _confidence_from_count(count: int) -> float:
    return round(min(0.95, 0.65 + count * 0.08), 2)


def _dedupe_insights(insights: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    result = []
    for insight in insights:
        key = (insight["title"], insight["metric_source"])
        if key in seen:
            continue
        seen.add(key)
        result.append(insight)
    return result


def _dedupe_actions(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result = []
    for action in actions:
        key = action.get("action") or ""
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(action)
    return result
