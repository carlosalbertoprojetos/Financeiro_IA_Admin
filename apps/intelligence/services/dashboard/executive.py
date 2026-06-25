"""Executive dashboard data aggregator for multiple audience levels."""

from __future__ import annotations

from typing import Any

from apps.intelligence.services.bottleneck_detector.detector import detect_bottlenecks
from apps.intelligence.services.executive_summary.agent import build_executive_summary
from apps.intelligence.services.kpi.engine import compute_board_kpis
from apps.intelligence.services.operational_score.scorer import compute_operational_score, get_score_history
from apps.intelligence.services.predictive.engine import predict_board
from apps.intelligence.services.risk_engine.scorer import assess_board_risk


def build_executive_dashboard(
    board_trello_id: str,
    *,
    level: str = "operational",
) -> dict[str, Any]:
    """
    Build dashboard payload for audience level.

    Levels: operational, management, director, ceo
    """
    kpis = compute_board_kpis(board_trello_id=board_trello_id)
    score = compute_operational_score(board_trello_id=board_trello_id, persist=False)
    risks = assess_board_risk(board_trello_id=board_trello_id)
    bottlenecks = detect_bottlenecks(board_trello_id=board_trello_id)
    predictions = predict_board(board_trello_id=board_trello_id)
    history = get_score_history(board_trello_id, limit=14)

    base = {
        "board_id": board_trello_id,
        "level": level,
        "operational_score": {"score": score.score, "level": score.level, "components": score.components},
        "score_history": history,
    }

    if level == "operational":
        return {
            **base,
            "lead_time": kpis.get("lead_time", {}).get("summary"),
            "cycle_time": kpis.get("cycle_time", {}).get("summary"),
            "wip": kpis.get("wip"),
            "throughput": kpis.get("throughput", {}).get("summary"),
            "bottlenecks": bottlenecks.get("stagnant_cards", [])[:10],
            "time_by_list": kpis.get("time_by_list"),
        }

    if level == "management":
        return {
            **base,
            "kpis": {
                "lead_time": kpis.get("lead_time", {}).get("summary"),
                "cycle_time": kpis.get("cycle_time", {}).get("summary"),
                "sla": kpis.get("sla"),
                "completion_rate": kpis.get("completion_rate"),
            },
            "team": kpis.get("team"),
            "risks": risks.get("assessments", [])[:10],
            "bottlenecks": bottlenecks,
            "predictions": predictions.get("predictions", [])[:10],
        }

    if level in ("director", "ceo"):
        summary = build_executive_summary(board_trello_id=board_trello_id, use_ai=False)
        payload = {
            **base,
            "executive_summary": summary.get("resumo_executivo"),
            "status": {
                "completed": summary.get("concluido"),
                "in_progress": summary.get("em_andamento"),
                "overdue": summary.get("atrasado"),
            },
            "top_risks": risks.get("assessments", [])[:5],
            "top_bottlenecks": bottlenecks.get("summary"),
            "priorities": summary.get("prioridades_imediatas", []),
            "trends": {"score_history": history},
        }
        if level == "ceo":
            payload["strategic_kpis"] = {
                "operational_score": score.score,
                "sla_compliance": kpis.get("sla"),
                "high_risk_cards": risks.get("high_risk_count"),
                "delay_predictions": predictions.get("high_delay_risk"),
            }
        return payload

    return base
