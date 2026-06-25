"""EOR Operational Score — proprietary 0-100 operational health indicator."""

from __future__ import annotations

from typing import Any

from django.utils import timezone

from apps.intelligence.domain.entities import OperationalScoreResult
from apps.intelligence.models import OperationalScoreSnapshot
from apps.intelligence.services.bottleneck_detector.detector import detect_bottlenecks
from apps.intelligence.services.kpi.engine import compute_board_kpis
from apps.intelligence.services.risk_engine.scorer import assess_board_risk
from integrations.trello.models import Board


def compute_operational_score(
    *,
    board_trello_id: str,
    persist: bool = True,
) -> OperationalScoreResult:
    """Compute EOR Operational Score (0-100) with component breakdown."""
    kpis = compute_board_kpis(board_trello_id=board_trello_id)
    risks = assess_board_risk(board_trello_id=board_trello_id)
    bottlenecks = detect_bottlenecks(board_trello_id=board_trello_id)

    delivery = _score_delivery(kpis)
    deadline = _score_deadline(kpis)
    quality = _score_quality(kpis)
    communication = 70
    execution = _score_execution(kpis, bottlenecks)
    risk_component = _score_risks(risks)
    productivity = _score_productivity(kpis)

    components = {
        "delivery": delivery,
        "deadline": deadline,
        "quality": quality,
        "communication": communication,
        "execution": execution,
        "risks": risk_component,
        "productivity": productivity,
    }

    weights = {
        "delivery": 0.20,
        "deadline": 0.20,
        "quality": 0.10,
        "communication": 0.10,
        "execution": 0.15,
        "risks": 0.15,
        "productivity": 0.10,
    }

    score = round(sum(components[k] * weights[k] for k in components))
    level = _score_to_color(score)

    result = OperationalScoreResult(
        board_id=board_trello_id,
        score=score,
        level=level,
        components=components,
    )

    if persist:
        board = Board.objects.get(trello_id=board_trello_id)
        OperationalScoreSnapshot.objects.create(
            board=board,
            score=score,
            level=level,
            delivery=delivery,
            deadline=deadline,
            quality=quality,
            communication=communication,
            execution=execution,
            risks=risk_component,
            productivity=productivity,
            details_json={"components": components, "weights": weights},
        )

    return result


def get_score_history(board_trello_id: str, limit: int = 30) -> list[dict[str, Any]]:
    snapshots = OperationalScoreSnapshot.objects.filter(
        board__trello_id=board_trello_id
    ).order_by("-created_at")[:limit]
    return [
        {
            "score": s.score,
            "level": s.level,
            "created_at": s.created_at.isoformat(),
            "components": {
                "delivery": s.delivery,
                "deadline": s.deadline,
                "quality": s.quality,
                "communication": s.communication,
                "execution": s.execution,
                "risks": s.risks,
                "productivity": s.productivity,
            },
        }
        for s in snapshots
    ]


def _score_delivery(kpis: dict) -> int:
    rate = kpis.get("completion_rate") or kpis.get("overview", {}).get("completion_rate")
    if rate is None:
        return 50
    return min(100, max(0, int(float(rate) * 100)))


def _score_deadline(kpis: dict) -> int:
    sla = kpis.get("sla", {})
    pct = sla.get("on_time_pct")
    if pct is None:
        delay = kpis.get("delay_rate", {}).get("summary", {}).get("rate", 0)
        return max(0, int(100 - (delay or 0) * 100))
    return min(100, max(0, int(pct)))


def _score_quality(kpis: dict) -> int:
    rework = kpis.get("rework_rate", {}).get("summary", {}).get("rate", 0) or 0
    return max(0, int(100 - rework * 200))


def _score_execution(kpis: dict, bottlenecks: dict) -> int:
    stagnant = len(bottlenecks.get("stagnant_cards", []))
    wip = kpis.get("wip") or kpis.get("overview", {}).get("wip") or 0
    penalty = min(50, stagnant * 5 + max(0, wip - 20))
    return max(0, 100 - penalty)


def _score_risks(risks: dict) -> int:
    avg = risks.get("average_score", 0)
    return max(0, int(100 - avg))


def _score_productivity(kpis: dict) -> int:
    throughput = kpis.get("throughput", {}).get("summary", {}).get("count", 0)
    if throughput >= 10:
        return 90
    if throughput >= 5:
        return 75
    if throughput >= 1:
        return 60
    return 40


def _score_to_color(score: int) -> str:
    if score >= 80:
        return "Verde"
    if score >= 60:
        return "Amarelo"
    if score >= 40:
        return "Laranja"
    return "Vermelho"
