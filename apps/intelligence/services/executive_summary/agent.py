"""Executive summary AI agent — produces structured executive narrative."""

from __future__ import annotations

from typing import Any

from django.utils import timezone

from ai.analyst import analyze_metrics, compact_metrics
from apps.intelligence.services.bottleneck_detector.detector import detect_bottlenecks
from apps.intelligence.services.knowledge.extractor import get_knowledge_base
from apps.intelligence.services.kpi.engine import compute_board_kpis
from apps.intelligence.services.predictive.engine import predict_board
from apps.intelligence.services.risk_engine.scorer import assess_board_risk
from integrations.trello.models import Board, Card


def build_executive_summary(
    *,
    board_trello_id: str,
    use_ai: bool = True,
    api_key: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Build structured executive summary for a board."""
    board = Board.objects.filter(trello_id=board_trello_id).first()
    if not board:
        return {"error": "Board not found", "board_id": board_trello_id}

    ref = timezone.now()
    kpis = compute_board_kpis(board_trello_id=board_trello_id)
    bottlenecks = detect_bottlenecks(board_trello_id=board_trello_id)
    risks = assess_board_risk(board_trello_id=board_trello_id)
    predictions = predict_board(board_trello_id=board_trello_id)
    knowledge = get_knowledge_base(board_trello_id)

    completed = Card.objects.filter(board=board, is_closed=True, is_removed=False).count()
    in_progress = Card.objects.filter(board=board, is_closed=False, is_removed=False).count()
    overdue = Card.objects.filter(
        board=board, is_closed=False, is_removed=False, due_at__lt=ref
    ).count()

    summary = {
        "board_id": board_trello_id,
        "board_name": board.name,
        "generated_at": ref.isoformat(),
        "resumo_executivo": _build_rule_based_summary(completed, in_progress, overdue, risks, bottlenecks),
        "concluido": {"count": completed, "description": f"{completed} cards concluídos"},
        "em_andamento": {"count": in_progress, "description": f"{in_progress} cards em andamento"},
        "atrasado": {"count": overdue, "description": f"{overdue} cards com prazo vencido"},
        "principais_riscos": risks.get("assessments", [])[:5],
        "principais_gargalos": bottlenecks.get("summary", ""),
        "dependencias_criticas": _extract_critical_dependencies(board_trello_id),
        "necessidades_decisao": _extract_decision_needs(predictions),
        "prioridades_imediatas": _build_priorities(risks, bottlenecks, overdue),
        "proximas_acoes": _build_recommendations(bottlenecks, risks, kpis),
        "kpis_snapshot": compact_metrics(kpis),
        "knowledge_highlights": knowledge[:5],
    }

    if use_ai:
        try:
            ai_diagnosis = analyze_metrics(kpis, api_key=api_key, model=model)
            summary["ai_diagnosis"] = ai_diagnosis
            summary["resumo_executivo"] = ai_diagnosis.get("executive_summary", summary["resumo_executivo"])
        except Exception as exc:
            summary["ai_error"] = str(exc)

    return summary


def _build_rule_based_summary(
    completed: int,
    in_progress: int,
    overdue: int,
    risks: dict,
    bottlenecks: dict,
) -> str:
    parts = [
        f"Operação com {completed} entregas concluídas e {in_progress} demandas ativas.",
    ]
    if overdue:
        parts.append(f"{overdue} item(ns) em atraso requerem atenção.")
    high_risk = risks.get("high_risk_count", 0)
    if high_risk:
        parts.append(f"{high_risk} card(s) em risco elevado.")
    bottleneck_summary = bottlenecks.get("summary", "")
    if bottleneck_summary and "Nenhum" not in bottleneck_summary:
        parts.append(f"Gargalos: {bottleneck_summary}.")
    return " ".join(parts)


def _extract_critical_dependencies(board_trello_id: str) -> list[str]:
    from apps.intelligence.services.communication_analysis.analyzer import analyze_board_communication

    deps: list[str] = []
    for analysis in analyze_board_communication(board_trello_id):
        deps.extend(analysis.external_dependencies)
    return list(dict.fromkeys(deps))[:10]


def _extract_decision_needs(predictions: dict) -> list[str]:
    needs: list[str] = []
    for pred in predictions.get("predictions", []):
        if pred.get("escalation_needed"):
            needs.append(f"Escalonamento recomendado para card {pred['card_id']}")
    return needs[:10]


def _build_priorities(risks: dict, bottlenecks: dict, overdue: int) -> list[str]:
    priorities: list[str] = []
    if overdue:
        priorities.append(f"Resolver {overdue} card(s) atrasado(s)")
    for item in risks.get("assessments", [])[:3]:
        if item["score"] >= 50:
            priorities.append(f"Mitigar risco {item['level']} no card {item['card_id']}")
    for item in bottlenecks.get("stagnant_cards", [])[:3]:
        priorities.append(f"Desbloquear card estagnado: {item['title'][:60]}")
    return priorities


def _build_recommendations(bottlenecks: dict, risks: dict, kpis: dict) -> list[dict[str, str]]:
    recs: list[dict[str, str]] = []

    if bottlenecks.get("congested_lists"):
        recs.append(
            {
                "title": "Reduzir WIP",
                "action": "Limitar cards nas listas congestionadas",
                "priority": "high",
            }
        )
    if risks.get("high_risk_count", 0) > 0:
        recs.append(
            {
                "title": "Revisão de riscos",
                "action": "Realizar review dos cards de alto risco",
                "priority": "high",
            }
        )
    delay = kpis.get("delay_rate", {}).get("summary", {})
    if delay.get("rate") and delay["rate"] > 0.2:
        recs.append(
            {
                "title": "Melhorar previsibilidade",
                "action": "Analisar causas de atraso e ajustar estimativas",
                "priority": "medium",
            }
        )
    return recs
