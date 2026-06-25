from __future__ import annotations

from typing import Any

from apps.intelligence.services.decision_layer.models import (
    DecisionObject,
    DecisionPriority,
    ExecutionMode,
    RecommendedAction,
)
from apps.intelligence.services.organizational_learning.patterns.analyzer import get_action_historical_stats
from apps.intelligence.services.organizational_learning.playbooks.engine import find_playbook_for_context

ACTION_TYPES = frozenset({
    "REASSIGN_OWNER",
    "ESCALATE_TASK",
    "REOPEN_CARD",
    "CREATE_ALERT",
    "ADJUST_PRIORITY",
    "MANAGERIAL_INTERVENTION",
    "ADD_COMMENT",
    "MOVE_CARD",
    "WEBHOOK_NOTIFY",
})


def generate_actions_from_entity(entity: dict[str, Any], *, board_id: str = "") -> list[RecommendedAction]:
    """Convert a semantic entity into structured recommended actions."""
    actions: list[RecommendedAction] = []
    card_id = entity.get("card_id", "")
    risk_score = entity.get("risk_score", 0) or 0
    risk_flags = entity.get("risk_flags") or []
    entity_type = entity.get("entity_type", "")
    title = entity.get("title", "")

    if risk_score >= 75:
        actions.append(_action_with_history(
            action_type="ESCALATE_TASK",
            description=f"Escalate critical-risk item: {title}",
            execution_mode=ExecutionMode.SEMI_AUTOMATIC.value,
            params={"reason": "critical_risk", "risk_score": risk_score},
            target_card_id=card_id,
            target_board_id=board_id,
            category=entity.get("category", ""),
        ))
        actions.append(_action_with_history(
            action_type="CREATE_ALERT",
            description=f"Create alert for critical risk on {title}",
            execution_mode=ExecutionMode.AUTOMATIC.value,
            params={"severity": "CRITICAL", "risk_score": risk_score},
            target_card_id=card_id,
            target_board_id=board_id,
            category=entity.get("category", ""),
        ))

    if risk_score >= 50:
        actions.append(_action_with_history(
            action_type="ADJUST_PRIORITY",
            description=f"Raise priority for high-risk item: {title}",
            execution_mode=ExecutionMode.SEMI_AUTOMATIC.value,
            params={"priority": "HIGH", "risk_score": risk_score},
            target_card_id=card_id,
            target_board_id=board_id,
            category=entity.get("category", ""),
        ))

    if "assignee_churn" in risk_flags or "excessive_handoffs" in risk_flags:
        actions.append(RecommendedAction(
            action_type="REASSIGN_OWNER",
            description=f"Review ownership — frequent reassignments on {title}",
            execution_mode=ExecutionMode.MANUAL.value,
            params={"reason": "assignee_churn"},
            target_card_id=card_id,
            target_board_id=board_id,
        ))

    if "stagnant" in risk_flags or entity.get("status") == "DELAYED":
        actions.append(RecommendedAction(
            action_type="MANAGERIAL_INTERVENTION",
            description=f"Manager review needed — stagnant or delayed: {title}",
            execution_mode=ExecutionMode.MANUAL.value,
            params={"reason": "stagnant_or_delayed"},
            target_card_id=card_id,
            target_board_id=board_id,
        ))

    if entity_type == "INCIDENT" and risk_score >= 60:
        actions.append(RecommendedAction(
            action_type="ADD_COMMENT",
            description=f"Add incident follow-up comment on {title}",
            execution_mode=ExecutionMode.AUTOMATIC.value,
            params={"text": "Incident flagged by EOR — review required."},
            target_card_id=card_id,
            target_board_id=board_id,
        ))

    if entity.get("status") == "COMPLETED" and "reopened" in risk_flags:
        actions.append(RecommendedAction(
            action_type="REOPEN_CARD",
            description=f"Reopen card after regression: {title}",
            execution_mode=ExecutionMode.SEMI_AUTOMATIC.value,
            params={"reason": "regression_detected"},
            target_card_id=card_id,
            target_board_id=board_id,
        ))

    playbook = find_playbook_for_context(
        category=entity.get("category", ""),
        risk_score=risk_score,
        board_id=board_id,
    )
    if playbook:
        pb_action = playbook.get("recommended_action", "")
        if pb_action and not any(a.action_type == pb_action for a in actions):
            actions.insert(0, _action_with_history(
                action_type=pb_action,
                description=f"Playbook recommendation ({playbook.get('historical_effectiveness_pct')}% historical success)",
                execution_mode=ExecutionMode.SEMI_AUTOMATIC.value,
                params={
                    "playbook_id": playbook.get("id"),
                    "historical_success_rate_pct": playbook.get("historical_effectiveness_pct"),
                },
                target_card_id=card_id,
                target_board_id=board_id,
                category=entity.get("category", ""),
            ))

    return _rank_actions_by_effectiveness(actions, category=entity.get("category", ""), board_id=board_id)


def generate_actions_from_insight(insight: str, *, board_id: str = "", context: dict[str, Any] | None = None) -> list[RecommendedAction]:
    """Convert a domain insight string into actionable recommendations."""
    ctx = context or {}
    actions: list[RecommendedAction] = []

    lower = insight.lower()
    if "assignee" in lower or "handoff" in lower:
        actions.append(RecommendedAction(
            action_type="MANAGERIAL_INTERVENTION",
            description="Review assignee handoff process",
            execution_mode=ExecutionMode.MANUAL.value,
            params={"insight": insight},
            target_board_id=board_id,
        ))
    if "blocked" in lower or "bottleneck" in lower:
        actions.append(RecommendedAction(
            action_type="ESCALATE_TASK",
            description="Escalate blocked workflow items",
            execution_mode=ExecutionMode.SEMI_AUTOMATIC.value,
            params={"insight": insight},
            target_board_id=board_id,
        ))
    if "incident" in lower or "risk" in lower:
        actions.append(RecommendedAction(
            action_type="CREATE_ALERT",
            description="Create operational alert from insight",
            execution_mode=ExecutionMode.AUTOMATIC.value,
            params={"insight": insight, "severity": "HIGH"},
            target_board_id=board_id,
        ))

    if not actions:
        actions.append(RecommendedAction(
            action_type="MANAGERIAL_INTERVENTION",
            description=f"Review insight: {insight[:120]}",
            execution_mode=ExecutionMode.MANUAL.value,
            params={"insight": insight, **ctx},
            target_board_id=board_id,
        ))

    return actions


def generate_decisions_from_output(
    output: dict[str, Any],
    *,
    source_trace_id: str = "",
    owner: str = "system",
) -> list[DecisionObject]:
    """Generate decision objects from query/intelligence pipeline output."""
    board_id = output.get("summary", {}).get("board_id", "")
    decisions: list[DecisionObject] = []
    seen_cards: set[str] = set()

    for entity in output.get("entities", []):
        card_id = entity.get("card_id", "")
        if card_id in seen_cards:
            continue
        seen_cards.add(card_id)
        actions = generate_actions_from_entity(entity, board_id=board_id)
        if not actions:
            continue
        risk_score = entity.get("risk_score", 0) or 0
        priority = _risk_to_priority(risk_score)
        decisions.append(DecisionObject.create(
            insight=f"Risk detected on {entity.get('title', card_id)} (score={risk_score})",
            source_trace_id=source_trace_id,
            priority=priority,
            recommended_actions=actions,
            owner=owner,
            board_id=board_id,
            context={"entity": entity, "entity_type": entity.get("entity_type")},
            score=float(risk_score),
        ))

    metrics = output.get("business_metrics") or {}
    risk_exposure = (metrics.get("risk_exposure_index") or {}).get("value", 0)
    if risk_exposure and float(risk_exposure) >= 70:
        actions = [RecommendedAction(
            action_type="CREATE_ALERT",
            description="Board-level risk exposure exceeds threshold",
            execution_mode=ExecutionMode.SEMI_AUTOMATIC.value,
            params={"risk_exposure_index": risk_exposure},
            target_board_id=board_id,
        )]
        decisions.append(DecisionObject.create(
            insight=f"Board risk exposure index at {risk_exposure}",
            source_trace_id=source_trace_id,
            priority=DecisionPriority.HIGH.value,
            recommended_actions=actions,
            owner=owner,
            board_id=board_id,
            context={"business_metrics": metrics},
            score=float(risk_exposure),
        ))

    for insight in output.get("domain_insights", [])[:5]:
        actions = generate_actions_from_insight(insight, board_id=board_id)
        decisions.append(DecisionObject.create(
            insight=insight,
            source_trace_id=source_trace_id,
            priority=DecisionPriority.MEDIUM.value,
            recommended_actions=actions,
            owner=owner,
            board_id=board_id,
            context={"source": "domain_intelligence"},
            score=40.0,
        ))

    return decisions


def _risk_to_priority(risk_score: float) -> str:
    if risk_score >= 75:
        return DecisionPriority.CRITICAL.value
    if risk_score >= 50:
        return DecisionPriority.HIGH.value
    if risk_score >= 25:
        return DecisionPriority.MEDIUM.value
    return DecisionPriority.LOW.value


def _action_with_history(
    *,
    action_type: str,
    description: str,
    execution_mode: str,
    params: dict[str, Any],
    target_card_id: str = "",
    target_board_id: str = "",
    category: str = "",
) -> RecommendedAction:
    """Attach historical effectiveness stats to action params (recommendation evolution)."""
    stats = get_action_historical_stats(action_type, category=category, board_id=target_board_id)
    enriched_params = dict(params)
    if stats["sample_size"] > 0:
        enriched_params["historical_success_rate_pct"] = stats["success_rate_pct"]
        enriched_params["historical_avg_risk_reduction_pct"] = stats["avg_risk_reduction_pct"]
        enriched_params["historical_sample_size"] = stats["sample_size"]
        if stats["success_rate_pct"] is not None:
            description = f"{description} [historical success: {stats['success_rate_pct']}%]"
    return RecommendedAction(
        action_type=action_type,
        description=description,
        execution_mode=execution_mode,
        params=enriched_params,
        target_card_id=target_card_id,
        target_board_id=target_board_id,
    )


def _rank_actions_by_effectiveness(
    actions: list[RecommendedAction],
    *,
    category: str = "",
    board_id: str = "",
) -> list[RecommendedAction]:
    """Sort actions by historical effectiveness when evidence exists."""
    def sort_key(action: RecommendedAction) -> float:
        rate = action.params.get("historical_success_rate_pct")
        if rate is not None:
            return float(rate)
        stats = get_action_historical_stats(action.action_type, category=category, board_id=board_id)
        return float(stats.get("avg_effectiveness") or 0)

    return sorted(actions, key=sort_key, reverse=True)
