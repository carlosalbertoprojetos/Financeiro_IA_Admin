"""Executive report builder — 14-section structured report."""

from __future__ import annotations

from typing import Any

from django.utils import timezone

from apps.intelligence.services.bottleneck_detector.detector import detect_bottlenecks
from apps.intelligence.services.communication_analysis.analyzer import analyze_board_communication
from apps.intelligence.services.description_intelligence.summary import aggregate_description_intelligence
from apps.intelligence.services.executive_summary.agent import build_executive_summary
from apps.intelligence.services.knowledge.extractor import get_knowledge_base
from apps.intelligence.services.kpi.engine import compute_board_kpis
from apps.intelligence.services.operational_score.scorer import compute_operational_score, get_score_history
from apps.intelligence.services.predictive.engine import predict_board
from apps.intelligence.services.risk_engine.scorer import assess_board_risk
from apps.intelligence.services.timeline.engine import build_card_timeline
from integrations.trello.models import Board, Card


def build_executive_report(board_trello_id: str, *, use_ai: bool = True) -> dict[str, Any]:
    """Build complete 14-section executive report."""
    board = Board.objects.filter(trello_id=board_trello_id).first()
    if not board:
        return {"error": "Board not found"}

    ref = timezone.now()
    summary = build_executive_summary(board_trello_id=board_trello_id, use_ai=use_ai)
    kpis = compute_board_kpis(board_trello_id=board_trello_id)
    bottlenecks = detect_bottlenecks(board_trello_id=board_trello_id)
    risks = assess_board_risk(board_trello_id=board_trello_id)
    predictions = predict_board(board_trello_id=board_trello_id)
    score = compute_operational_score(board_trello_id=board_trello_id)
    knowledge = get_knowledge_base(board_trello_id)
    communications = analyze_board_communication(board_trello_id)
    description_intelligence = aggregate_description_intelligence(
        list(Card.objects.filter(board=board, is_removed=False).select_related("board_list")[:500])
    )

    timeline = _build_board_timeline(board)
    checklists = _build_checklist_summary(board)
    trends = _build_trends(board_trello_id, kpis)

    return {
        "meta": {
            "board_id": board_trello_id,
            "board_name": board.name,
            "generated_at": ref.isoformat(),
            "version": "EOR_V2",
        },
        "1_resumo_executivo": summary.get("resumo_executivo", ""),
        "2_status_geral": {
            "concluido": summary.get("concluido"),
            "em_andamento": summary.get("em_andamento"),
            "atrasado": summary.get("atrasado"),
            "operational_score": {"score": score.score, "level": score.level},
        },
        "3_timeline": timeline,
        "4_kpis": kpis,
        "5_gargalos": bottlenecks,
        "6_riscos": risks,
        "7_comunicacao": [
            {
                "card_id": c.card_id,
                "summary": c.executive_summary,
                "decisions": list(c.decisions),
                "risks": list(c.risks),
            }
            for c in communications[:20]
        ],
        "8_checklists": checklists,
        "9_tendencias": trends,
        "10_licoes_aprendidas": [k for k in knowledge if k["type"] == "lesson_learned"][:10],
        "11_recomendacoes": summary.get("proximas_acoes", []),
        "12_proximas_acoes": summary.get("prioridades_imediatas", []),
        "13_score_operacional": {
            "score": score.score,
            "level": score.level,
            "components": score.components,
            "history": get_score_history(board_trello_id, limit=7),
        },
        "14_anexos": {
            "predictions": predictions,
            "knowledge_base": knowledge,
            "ai_diagnosis": summary.get("ai_diagnosis"),
        },
        "15_description_intelligence": {
            "resumo_executivo_expandido": _build_expanded_description_summary(description_intelligence),
            "classificacao_operacional": {
                "quantidade_por_categoria": description_intelligence["categories"],
                "quantidade_por_entidade": description_intelligence["entities_by_type"],
                "eventos_extraidos": description_intelligence["events_by_type"],
            },
            "indicadores_operacionais_avancados": kpis.get("description_intelligence", {}).get("kpis", {}),
            "dashboards": description_intelligence["dashboards"],
            "qualidade": {
                "description_quality_score": description_intelligence["avg_description_quality_score"],
                "cards_com_descricao": description_intelligence["cards_with_description"],
                "cards_analisados": description_intelligence["cards_analyzed"],
            },
            "rastreabilidade": [
                {
                    "card_id": analysis["card_id"],
                    "title": analysis["card_title"],
                    "summary": analysis["expanded_summary"],
                    "quality": analysis["quality"],
                }
                for analysis in description_intelligence["analyses"][:50]
            ],
        },
    }


def _build_board_timeline(board: Board, limit: int = 50) -> list[dict[str, Any]]:
    from apps.intelligence.models import TimelineEvent

    events = TimelineEvent.objects.filter(board=board).order_by("-event_timestamp")[:limit]
    return [
        {
            "event_type": e.event_type,
            "timestamp": e.event_timestamp.isoformat(),
            "actor": e.actor,
            "card_id": e.card.trello_id if e.card else None,
            "payload": e.payload_json,
        }
        for e in events
    ]


def _build_checklist_summary(board: Board) -> list[dict[str, Any]]:
    from apps.intelligence.services.checklist.intelligence import analyze_checklists

    cards = Card.objects.filter(board=board, is_removed=False)[:30]
    return [
        {
            "card_id": card.trello_id,
            "title": card.title,
            **analyze_checklists(card).__dict__,
        }
        for card in cards
        if analyze_checklists(card).total_items > 0
    ]


def _build_trends(board_trello_id: str, kpis: dict) -> dict[str, Any]:
    history = get_score_history(board_trello_id, limit=14)
    return {
        "score_trend": [{"date": h["created_at"], "score": h["score"]} for h in history],
        "throughput": kpis.get("throughput", {}),
        "aging": kpis.get("aging", {}),
    }


def _build_expanded_description_summary(description_intelligence: dict[str, Any]) -> dict[str, Any]:
    summaries = [
        analysis["expanded_summary"]
        for analysis in description_intelligence.get("analyses", [])
    ]
    fields = ("objetivo", "contexto", "problema", "solucao", "resultado", "impacto")
    return {
        field: [summary[field] for summary in summaries if summary.get(field)][:10]
        for field in fields
    }
