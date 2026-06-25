from __future__ import annotations

import logging
from typing import Any

from apps.intelligence.models import DecisionEffectivenessRecord
from apps.intelligence.services.organizational_learning.memory.storage import record_lesson_from_effectiveness
from apps.intelligence.services.organizational_learning.models import DecisionEffectiveness
from apps.intelligence.services.organizational_learning.outcomes.evaluator import evaluate_action_outcome
from apps.intelligence.services.organizational_learning.scoring.effectiveness_scorer import compute_effectiveness_score

logger = logging.getLogger(__name__)


def record_action_learning(
    *,
    decision_id: str,
    action_type: str,
    before: dict[str, Any],
    after: dict[str, Any],
    impact: dict[str, Any],
    execution_time_ms: int = 0,
    board_id: str = "",
    category: str = "",
    owner: str = "",
    context: dict[str, Any] | None = None,
) -> DecisionEffectiveness | None:
    """
    OLE pipeline hook — record effectiveness after every executed action.
    All scores derived from real before/after measurements.
    """
    outcome = evaluate_action_outcome(
        action_type=action_type,
        before=before,
        after=after,
        impact=impact,
    )
    outcome_score, effectiveness_score = compute_effectiveness_score(
        outcome,
        execution_time_ms=execution_time_ms,
        bottleneck_resolved=context.get("bottleneck_resolved", False) if context else False,
    )

    effectiveness = DecisionEffectiveness(
        decision_id=decision_id,
        action_type=action_type,
        risk_before=outcome["risk_before"],
        risk_after=outcome["risk_after"],
        sla_before=outcome["sla_before"],
        sla_after=outcome["sla_after"],
        execution_time=execution_time_ms,
        outcome_score=outcome_score,
        effectiveness_score=effectiveness_score,
        outcome_label=outcome["outcome_label"],
        board_id=board_id,
        category=category or "GENERAL",
        owner=owner,
        context=context,
    )

    try:
        record = DecisionEffectivenessRecord.objects.create(
            decision_id=decision_id,
            action_type=action_type,
            risk_before=effectiveness.risk_before,
            risk_after=effectiveness.risk_after,
            sla_before=effectiveness.sla_before,
            sla_after=effectiveness.sla_after,
            execution_time=execution_time_ms,
            outcome_score=outcome_score,
            effectiveness_score=effectiveness_score,
            outcome_label=outcome["outcome_label"],
            board_id=board_id,
            category=category or "GENERAL",
            owner=owner,
            context_json={**(context or {}), "outcome": outcome},
        )
        record_dict = effectiveness.to_dict()
        record_dict["id"] = record.id
        record_lesson_from_effectiveness(record_dict)
        return effectiveness
    except Exception:
        logger.exception("Failed to persist decision effectiveness")
        return None


def build_executive_learning_dashboard(*, board_id: str = "") -> dict[str, Any]:
    """Executive dashboard for organizational learning."""
    from apps.intelligence.services.organizational_learning.maturity.index import compute_eor_maturity_index
    from apps.intelligence.services.organizational_learning.patterns.analyzer import analyze_action_patterns
    from apps.intelligence.services.organizational_learning.playbooks.engine import generate_playbooks
    from apps.intelligence.services.organizational_learning.memory.storage import get_memory_history

    patterns = analyze_action_patterns(board_id=board_id)
    maturity = compute_eor_maturity_index(board_id=board_id)
    playbooks = generate_playbooks(board_id=board_id)
    memories = get_memory_history(board_id=board_id, limit=20)

    evolution = _effectiveness_evolution(board_id)

    narrative = _build_narrative(patterns)

    return {
        "dashboard": "executive_learning",
        "board_id": board_id or "all",
        "eor_maturity_index": maturity,
        "best_actions": patterns.get("most_effective_actions", []),
        "worst_actions": patterns.get("least_effective_actions", []),
        "action_patterns": patterns,
        "playbooks": playbooks[:10],
        "organizational_memory": memories,
        "effectiveness_evolution": evolution,
        "narrative": narrative,
    }


def _effectiveness_evolution(board_id: str) -> list[dict[str, Any]]:
    from django.db.models.functions import TruncMonth
    from django.db.models import Avg, Count

    qs = DecisionEffectivenessRecord.objects.all()
    if board_id:
        qs = qs.filter(board_id=board_id)

    monthly = (
        qs.annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(avg_effectiveness=Avg("effectiveness_score"), count=Count("id"))
        .order_by("month")
    )
    return [
        {
            "month": row["month"].isoformat() if row["month"] else "",
            "avg_effectiveness": round(row["avg_effectiveness"] or 0, 1),
        }
        for row in monthly
    ]


def _build_narrative(patterns: dict[str, Any]) -> list[str]:
    """Evidence-based narrative statements — no invented data."""
    narratives = []
    for action in patterns.get("most_effective_actions", [])[:3]:
        if action.get("executions", 0) >= 1:
            narratives.append(
                f"Action {action['action_type']} has {action.get('success_rate_pct', 0)}% success rate "
                f"across {action['executions']} executions, with average risk reduction of "
                f"{action.get('avg_risk_reduction_pct', 0)}%."
            )
    if not narratives:
        narratives.append("Insufficient historical data to generate evidence-based narratives.")
    return narratives
