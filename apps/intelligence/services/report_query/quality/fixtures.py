from __future__ import annotations

import base64
import json
from copy import deepcopy
from typing import Any


def build_quality_gate_fixture(*, variant: str = "complete") -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    report = _complete_report()
    if variant == "missing_story":
        report.pop("executive_story", None)
        report.pop("executive_story_quality_score", None)
    exports = _exports(report)
    return report, exports


def _complete_report() -> dict[str, Any]:
    executive_brief = {
        "status": "Atencao executiva",
        "summary": (
            "A operacao de suporte B2B esta sob pressao de SLA: metade do recorte esta vencida, "
            "37,5% dos cards nao possuem responsavel e a qualidade das descricoes limita a triagem."
        ),
        "kpis": [
            {"label": "Cards analisados", "value": "8", "direction": "estavel", "confidence": 0.96},
            {"label": "SLA compliance", "value": "50%", "direction": "piorou", "confidence": 0.84},
            {"label": "Cards vencidos", "value": "4", "direction": "piorou", "confidence": 0.88},
            {"label": "Sem responsavel", "value": "3", "direction": "piorou", "confidence": 0.8},
            {"label": "Descricoes incompletas", "value": "5", "direction": "piorou", "confidence": 0.82},
        ],
        "top_risks": [
            "Incidente ERP financeiro vencido e sem replanejamento formal.",
            "Solicitacao de integracao fiscal sem responsavel definido.",
            "Descricoes incompletas aumentando dependencia de alinhamentos manuais.",
        ],
        "top_opportunities": [
            "Criar playbook para incidentes vencidos.",
            "Implantar checklist minimo de abertura.",
            "Revisar diariamente cards sem dono.",
        ],
        "top_decisions": [
            "Repriorizar incidentes vencidos ainda hoje.",
            "Definir responsaveis para todos os cards em ate 24h.",
            "Exigir descricao minima para novas demandas em 7 dias.",
        ],
        "action_plan": [
            "War room de 30 minutos para replanejar vencidos.",
            "Triagem de ownership antes do proximo ciclo operacional.",
            "Checklist minimo: objetivo, prazo, dono e proximo passo.",
        ],
    }
    scorecard = {
        "overall_score": 72,
        "label": "atencao",
        "confidence": 0.84,
        "dimensions": [
            {"name": "Saude Operacional", "score": 68, "status": "atencao", "evidence": "4 de 8 cards vencidos"},
            {"name": "Qualidade", "score": 62, "status": "critico", "evidence": "5 descricoes incompletas"},
            {"name": "Produtividade", "score": 74, "status": "bom", "evidence": "8 cards no recorte com plano de acao definido"},
            {"name": "Comunicacao", "score": 70, "status": "atencao", "evidence": "comentarios existem, mas nao fecham todas as decisoes"},
            {"name": "Documentacao", "score": 58, "status": "critico", "evidence": "descricoes incompletas limitam rastreabilidade"},
            {"name": "Risco", "score": 64, "status": "atencao", "evidence": "2 riscos prioritarios identificados"},
            {"name": "Execucao", "score": 73, "status": "bom", "evidence": "acoes recomendadas possuem dono e prazo"},
            {"name": "Maturidade", "score": 75, "status": "bom", "evidence": "quality gate e baseline ativos"},
        ],
    }
    benchmark = {
        "current_period": "ultimos 7 dias",
        "previous_period": "7 dias anteriores",
        "last_90_days": "historico demonstrativo",
        "items": [
            {"metric": "SLA compliance", "current": "50%", "previous": "62%", "last_90_days": "68%", "trend": "piorou"},
            {"metric": "Cards vencidos", "current": "4", "previous": "3", "last_90_days": "2,4 media", "trend": "piorou"},
            {"metric": "Cards sem responsavel", "current": "3", "previous": "2", "last_90_days": "1,8 media", "trend": "piorou"},
            {"metric": "Comentarios conclusivos", "current": "3", "previous": "3", "last_90_days": "sem dados suficientes", "trend": "estavel"},
        ],
        "summary": "SLA, ownership e documentacao pioraram no periodo; comunicacao ficou estavel.",
        "confidence": 0.78,
    }
    story = {
        "headline": "Incidentes vencidos passaram a concentrar o risco executivo da operacao.",
        "period_story": (
            "O periodo analisou 8 cards da operacao de suporte B2B. O principal desvio foi a concentracao "
            "de 4 cards vencidos, combinada a 3 cards sem responsavel e 5 descricoes incompletas. "
            "Isso reduz previsibilidade, aumenta risco de SLA e obriga a gestao a decidir hoje quais "
            "incidentes serao replanejados, quem assume cada demanda e qual padrao minimo de abertura sera exigido."
        ),
        "generated": True,
        "key_drivers": [
            {
                "title": "Cards vencidos concentram risco operacional",
                "explanation": "Metade do recorte esta vencida e ainda aberta, o que reduz previsibilidade e pressiona SLA.",
                "evidence": ["4 de 8 cards estao abertos e vencidos"],
                "impact": 4,
                "recommended_action": "Replanejar cards vencidos hoje.",
                "confidence": 0.88,
                "operational_impact": "fila critica permanece sem criterio de recuperacao",
                "deadline_impact": "maior probabilidade de rompimento de SLA nas proximas 48h",
                "productivity_impact": "gestores gastam mais tempo reagindo a urgencias",
                "strategic_impact": "queda de confianca no controle operacional",
            },
            {
                "title": "Descricoes incompletas limitam decisao",
                "explanation": "Descricoes sem objetivo, prazo, dono ou proximo passo atrasam triagem e aumentam retrabalho.",
                "evidence": ["5 descricoes incompletas"],
                "impact": 3,
                "recommended_action": "Exigir descricao minima.",
                "confidence": 0.82,
                "operational_impact": "triagem depende de perguntas adicionais",
                "deadline_impact": "decisoes ficam mais lentas quando o prazo ja esta pressionado",
                "productivity_impact": "mais interrupcoes para recuperar contexto",
                "strategic_impact": "menor qualidade de governanca sobre demandas criticas",
            },
            {
                "title": "Cards sem responsavel reduzem accountability",
                "explanation": "Demandas sem dono ficam sem acompanhamento claro e tendem a perder prioridade no fluxo.",
                "evidence": ["3 cards sem responsavel"],
                "impact": 3,
                "recommended_action": "Atribuir responsaveis.",
                "confidence": 0.8,
                "operational_impact": "execucao fica difusa e sem ponto unico de cobranca",
                "deadline_impact": "prazos podem vencer sem escalonamento",
                "productivity_impact": "a equipe duplica alinhamentos para descobrir ownership",
                "strategic_impact": "responsabilizacao gerencial fica fragil",
            },
        ],
        "decision_ready_summary": [
            {
                "decision": "Repriorizar cards vencidos.",
                "reason": "Atrasos abertos pressionam SLA.",
                "evidence": ["4 cards vencidos"],
                "consequence_if_no_action": "A exposicao operacional continua crescendo.",
                "urgency": "alta",
                "suggested_owner": "Gestor operacional",
                "suggested_deadline": "Hoje",
            },
            {
                "decision": "Atribuir responsaveis para cards sem dono.",
                "reason": "Demandas sem owner perdem accountability e atrasam escalonamento.",
                "evidence": ["3 cards sem responsavel"],
                "consequence_if_no_action": "Cards criticos podem continuar sem acompanhamento ate o proximo ciclo.",
                "urgency": "alta",
                "suggested_owner": "Lider da equipe",
                "suggested_deadline": "24h",
            },
            {
                "decision": "Exigir descricao minima.",
                "reason": "Descricoes incompletas reduzem rastreabilidade.",
                "evidence": ["5 descricoes incompletas"],
                "consequence_if_no_action": "Decisoes continuam dependendo de suposicao.",
                "urgency": "media",
                "suggested_owner": "Lider da equipe",
                "suggested_deadline": "7 dias",
            },
        ],
        "action_plan": [
            {
                "action": "Replanejar cards vencidos.",
                "owner": "Gestor operacional",
                "deadline": "Hoje",
                "evidence": ["4 cards vencidos"],
                "expected_result": "Reduzir risco de SLA.",
                "success_metric": "100% dos cards vencidos com novo prazo ou decisao registrada",
            },
            {
                "action": "Atribuir responsaveis para cards sem dono.",
                "owner": "Lider da equipe",
                "deadline": "24h",
                "evidence": ["3 cards sem responsavel"],
                "expected_result": "Melhorar accountability.",
                "success_metric": "0 cards criticos sem responsavel",
            },
            {
                "action": "Aplicar checklist minimo nas novas demandas.",
                "owner": "Coordenador operacional",
                "deadline": "7 dias",
                "evidence": ["5 descricoes incompletas"],
                "expected_result": "Reduzir retrabalho de triagem.",
                "success_metric": "90% dos novos cards com objetivo, prazo, dono e proximo passo",
            },
        ],
        "story_structure": {
            "contexto_periodo": {
                "summary": "8 cards analisados com incidentes e atrasos relevantes.",
                "evidence": ["total_cards=8"],
            },
            "fatores_resultado": {
                "summary": "Cards vencidos, descricoes incompletas e falta de responsavel explicam o resultado.",
                "evidence": ["4 cards vencidos", "5 descricoes incompletas", "3 sem responsavel"],
            },
            "decisoes_prioritarias": {
                "summary": "Repriorizar vencidos, atribuir responsaveis e exigir descricao minima.",
                "evidence": ["4 cards vencidos", "3 sem responsavel", "5 descricoes incompletas"],
            },
            "plano_acao": {
                "summary": "Replanejar vencidos, atribuir responsaveis e completar descricoes.",
                "evidence": ["4 cards vencidos", "3 sem responsavel"],
            },
            "riscos_se_nada_mudar": {
                "summary": "Risco crescente de rompimento de SLA se os vencidos nao forem tratados.",
                "evidence": ["overdue_open_cards=4"],
            },
        },
        "evidence_map": [
            {"source": "metrics_pack.sla.overdue_open_cards", "claim": "cards vencidos", "evidence": "4"},
            {"source": "metrics_pack.quality.incomplete_description_count", "claim": "descricao", "evidence": "5"},
            {"source": "metrics_pack.quality.missing_owner_count", "claim": "responsavel", "evidence": "3"},
            {"source": "executive_brief.kpis", "claim": "SLA compliance", "evidence": "50%"},
        ],
        "executive_story_quality_score": {
            "score": 88,
            "label": "executivo",
            "confidence": 0.88,
            "criteria": {},
            "justification": ["3 drivers priorizados", "3 decisoes prontas", "4 evidencias mapeadas"],
        },
    }
    analytical = {
        "metrics_pack": {
            "volume": {"total_cards": 8},
            "sla": {"overdue_open_cards": 4, "cards_without_due_date": 2, "cards_due_in_48h": 1, "compliance_pct": 50},
            "quality": {
                "missing_owner_count": 3,
                "incomplete_description_count": 5,
                "cards_with_pending_checklists": 4,
            },
            "communication": {"total_comments": 9, "cards_without_comments": 2},
            "risks": {
                "high_risk_cards": [
                    {
                        "card_id": "INC-ERP-042",
                        "title": "Incidente ERP financeiro vencido",
                        "risk_score": 82,
                        "reasons": ["Card vencido", "SLA pressionado"],
                    },
                    {
                        "card_id": "INT-FISCAL-017",
                        "title": "Integracao fiscal sem responsavel",
                        "risk_score": 75,
                        "reasons": ["Sem responsavel", "Descricao incompleta"],
                    },
                ]
            },
        },
        "activity_classification": {
            "cards": [
                {"card_id": "INC-ERP-042", "description_quality_score": 20},
                {"card_id": "INT-FISCAL-017", "description_quality_score": 30},
            ]
        },
        "recommendations": [
            {
                "priority": "alta",
                "action": "Replanejar cards vencidos.",
                "reason": "Ha itens fora do prazo.",
                "evidence": ["4 cards vencidos"],
            }
        ],
        "quality": {"report_quality_score": 82, "label": "bom"},
    }
    narrative = {
        "insights": [
            {
                "title": "Itens abertos vencidos pressionam SLA",
                "severity": "alta",
                "metric_source": "metrics_pack.sla.overdue_open_cards",
                "evidence": ["4 cards vencidos"],
                "recommended_action": "Replanejar cards vencidos.",
            }
        ],
        "executive_readability_score": {"score": 84, "label": "bom"},
    }
    discovery = {
        "report_intelligence_score": {"score": 86, "label": "executivo"},
        "what_happens_next": [
            {
                "scenario": "Risco crescente de rompimento de SLA.",
                "confidence": 0.76,
                "basis": ["4 cards vencidos"],
                "trend_observed": True,
            }
        ],
        "executive_highlights": [
            {
                "title": "Concentracao elevada de cards vencidos",
                "evidence": ["4 de 8 cards vencidos"],
                "impact": 4,
                "confidence": 0.9,
            }
        ],
        "executive_surprises": [
            {
                "text": "50% dos cards analisados concentram o principal risco de SLA.",
                "evidence": ["4 de 8 cards vencidos"],
                "confidence": 0.86,
            }
        ],
        "opportunities": [
            {
                "title": "Padronizar tratamento de incidentes vencidos",
                "recommended_action": "Criar playbook de incidente com SLA, dono e checklist minimo.",
                "evidence": ["4 cards vencidos", "categoria incidente recorrente"],
                "confidence": 0.84,
            },
            {
                "title": "Melhorar qualidade das descricoes",
                "recommended_action": "Exigir objetivo, prazo, responsavel e proximo passo em novos cards.",
                "evidence": ["5 descricoes incompletas"],
                "confidence": 0.82,
            },
        ],
        "hotspots": {
            "categorias": [{"name": "Incidentes", "count": 4}],
            "gargalos": [{"name": "Cards vencidos sem replanejamento", "count": 4}],
        },
    }
    return {
        "meta": {
            "board_id": "operacao-alpha-suporte-b2b",
            "board_name": "Operacao Alpha - Suporte B2B",
            "report_type": "EXECUTIVO",
            "matched_cards": 8,
            "period": "LAST_7_DAYS",
            "report_version": "1.0",
        },
        "data": {"report_type": "EXECUTIVO"},
        "metrics": {"sla": {"total": 8, "compliance_pct": 50}},
        "executive_brief": executive_brief,
        "operational_scorecard": scorecard,
        "internal_benchmark": benchmark,
        "analytical": analytical,
        "executive_narrative": narrative,
        "discovery": discovery,
        "executive_story": story,
        "report_quality_score": 82,
        "executive_readability_score": {"score": 84, "label": "bom"},
        "report_intelligence_score": {"score": 86, "label": "executivo"},
        "executive_story_quality_score": deepcopy(story["executive_story_quality_score"]),
        "cards": [
            {"card_id": "INC-ERP-042", "title": "Incidente ERP financeiro vencido", "status": "Em andamento", "risk_score": 82},
            {"card_id": "INT-FISCAL-017", "title": "Integracao fiscal sem responsavel", "status": "Backlog", "risk_score": 75},
        ],
    }


def _exports(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    markdown = "\n".join(
        [
            "# Relatorio fixture",
            "## Executive Brief",
            "## História Executiva",
            "## Scorecard Executivo",
            "## Top 3 Drivers",
            "## Decisões Prioritárias",
            "## Plano de Ação",
        ]
    ).encode("utf-8")
    pptx_outline = json.dumps(
        {
            "slides": [
                {"title": "História Executiva"},
                {"title": "Executive Brief"},
                {"title": "Scorecard Executivo"},
                {"title": "Top 3 Drivers"},
                {"title": "Decisões Prioritárias"},
                {"title": "Riscos se Nada Mudar"},
                {"title": "Plano de Ação"},
            ],
            "executive_story": report.get("executive_story"),
        },
        ensure_ascii=False,
    ).encode("utf-8")
    return {
        "json": report,
        "markdown": {
            "format": "markdown",
            "content_type": "text/markdown",
            "filename": "fixture-report.md",
            "content_base64": _b64(markdown),
            "size_bytes": len(markdown),
        },
        "pdf": {
            "format": "pdf",
            "content_type": "application/pdf",
            "filename": "fixture-report.pdf",
            "content_base64": _b64(b"%PDF-1.4 fixture executive report"),
            "size_bytes": 31,
        },
        "pptx": {
            "format": "pptx",
            "content_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "filename": "fixture-report-outline.json",
            "content_base64": _b64(pptx_outline),
            "size_bytes": len(pptx_outline),
        },
    }


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")
