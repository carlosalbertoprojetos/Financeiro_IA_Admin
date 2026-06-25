from __future__ import annotations

from typing import Any

from apps.intelligence.services.decision_layer.models import DecisionObject, DecisionPriority


PRIORITY_WEIGHT = {
    DecisionPriority.CRITICAL.value: 100,
    DecisionPriority.HIGH.value: 75,
    DecisionPriority.MEDIUM.value: 50,
    DecisionPriority.LOW.value: 25,
}


def compute_decision_score(decision: DecisionObject | dict[str, Any]) -> float:
    """Score a decision for queue ordering."""
    if isinstance(decision, DecisionObject):
        data = decision.to_dict()
    else:
        data = decision

    base = PRIORITY_WEIGHT.get(data.get("priority", "MEDIUM"), 50)
    score = data.get("score", 0) or 0
    context = data.get("context") or {}
    entity = context.get("entity") or {}

    urgency_boost = 0.0
    if entity.get("status") == "DELAYED":
        urgency_boost += 15
    if entity.get("severity") in ("CRITICAL", "HIGH"):
        urgency_boost += 10

    sla_boost = 0.0
    metrics = context.get("business_metrics") or {}
    sla_prob = (metrics.get("sla_breach_probability") or {}).get("value", 0)
    if sla_prob:
        sla_boost = min(20, float(sla_prob) * 0.2)

    dependency_boost = 0.0
    risk_flags = entity.get("risk_flags") or []
    if "external_dependency" in risk_flags:
        dependency_boost = 10

    action_count = len(data.get("recommended_actions") or [])
    action_penalty = min(5, action_count)

    return base + score * 0.3 + urgency_boost + sla_boost + dependency_boost - action_penalty


def prioritize_decisions(decisions: list[DecisionObject]) -> list[DecisionObject]:
    """Return decisions sorted by operational impact (highest first)."""
    for d in decisions:
        d.score = compute_decision_score(d)
    return sorted(decisions, key=lambda d: d.score, reverse=True)


def build_action_queue(decisions: list[DecisionObject]) -> list[dict[str, Any]]:
    """Build ordered action queue from prioritized decisions."""
    ordered = prioritize_decisions(decisions)
    queue: list[dict[str, Any]] = []
    rank = 1
    for decision in ordered:
        for action in decision.recommended_actions:
            queue.append({
                "rank": rank,
                "decision_id": decision.id,
                "priority": decision.priority,
                "score": decision.score,
                "insight": decision.insight,
                "action": action,
                "status": decision.status,
                "board_id": decision.board_id,
            })
            rank += 1
    return queue
