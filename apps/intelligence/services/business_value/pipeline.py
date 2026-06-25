from __future__ import annotations

import logging
from typing import Any

from apps.intelligence.models import BusinessValueRecordModel
from apps.intelligence.services.business_value.attribution.engine import aggregate_by_dimension
from apps.intelligence.services.business_value.config import base_impact_brl
from apps.intelligence.services.business_value.cost_engine.calculator import compute_operational_costs
from apps.intelligence.services.business_value.models import BusinessValueRecord
from apps.intelligence.services.business_value.productivity.engine import compute_productivity_value
from apps.intelligence.services.business_value.risk_value.engine import compute_avoided_loss, compute_expected_loss
from apps.intelligence.services.business_value.roi.engine import compute_action_roi
from apps.intelligence.services.business_value.trends.engine import compute_value_trends

logger = logging.getLogger(__name__)


def _enrich_card_state(card_id: str, state: dict[str, Any]) -> dict[str, Any]:
    """Add measurable fields from card ORM when available."""
    if not card_id:
        return state
    try:
        from integrations.trello.models import Card
        from django.utils import timezone

        card = Card.objects.filter(trello_id=card_id).select_related("board_list").prefetch_related("assignees").first()
        if not card:
            return state
        enriched = dict(state)
        enriched["assignee_count"] = card.assignees.count() or 1
        if card.due_at and not card.completed_at and card.due_at < timezone.now():
            enriched["days_overdue"] = (timezone.now() - card.due_at).days
        enriched["project"] = (card.board_list.name if card.board_list else "") or state.get("project", "")
        members = list(card.assignees.values_list("full_name", flat=True)[:1])
        enriched["member"] = members[0] if members else state.get("member", "")
        return enriched
    except Exception:
        return state


def record_action_value(
    *,
    decision_id: str,
    action_type: str,
    before: dict[str, Any],
    after: dict[str, Any],
    effectiveness: dict[str, Any] | None = None,
    board_id: str = "",
    category: str = "",
    team: str = "",
    project: str = "",
    member: str = "",
    execution_time_ms: int = 0,
    card_id: str = "",
) -> BusinessValueRecord | None:
    """
    BVE pipeline hook — compute and persist financial value after OLE learning.
    DAL → OLE → BVE
    """
    card_state = _enrich_card_state(card_id, {
        "risk_score": before.get("risk_score", 0),
        "sla_breach_probability": before.get("sla_breach_probability", before.get("risk_score", 0)),
        "days_overdue": before.get("days_overdue", 0),
    })

    impact_brl = base_impact_brl() * (before.get("risk_score", 0) / 100)
    avoided = compute_avoided_loss(
        risk_before=before.get("risk_score", 0),
        risk_after=after.get("risk_score", 0),
        impact_brl=impact_brl,
    )
    productivity = compute_productivity_value(
        risk_before=before.get("risk_score", 0),
        risk_after=after.get("risk_score", 0),
        execution_time_ms=execution_time_ms,
    )
    roi = compute_action_roi(
        action_type=action_type,
        avoided_loss=avoided["avoided_loss"],
        realized_benefit=productivity["estimated_benefit"],
    )
    costs = compute_operational_costs(card_state=card_state, impact_brl=impact_brl)
    total_op_cost = sum(c["estimated_cost"] for c in costs)

    confidence_values = [avoided["confidence_score"], productivity["confidence_score"], roi["confidence_score"]]
    if costs:
        confidence_values.append(sum(c["confidence_score"] for c in costs) / len(costs))
    confidence = round(sum(confidence_values) / len(confidence_values), 2)

    record = BusinessValueRecord(
        source_id=decision_id,
        source_type="action_execution",
        value_type="ACTION_ROI",
        estimated_cost=roi["action_cost"] + total_op_cost,
        estimated_benefit=avoided["avoided_loss"] + productivity["estimated_benefit"],
        realized_benefit=productivity["estimated_benefit"] if after.get("risk_score", 0) < before.get("risk_score", 0) else 0,
        avoided_loss=avoided["avoided_loss"],
        confidence_score=confidence,
        board_id=board_id,
        action_type=action_type,
        category=category or "GENERAL",
        team=team or card_state.get("team", ""),
        project=project or card_state.get("project", ""),
        member=member or card_state.get("member", ""),
        roi_pct=roi["roi_pct"],
        audit_json={
            "avoided_loss_detail": avoided,
            "productivity": productivity,
            "roi": roi,
            "operational_costs": costs,
            "effectiveness": effectiveness,
            "before": before,
            "after": after,
        },
    )

    try:
        BusinessValueRecordModel.objects.create(
            source_id=record.source_id,
            source_type=record.source_type,
            value_type=record.value_type,
            estimated_cost=record.estimated_cost,
            estimated_benefit=record.estimated_benefit,
            realized_benefit=record.realized_benefit,
            avoided_loss=record.avoided_loss,
            confidence_score=record.confidence_score,
            currency=record.currency,
            board_id=record.board_id,
            action_type=record.action_type,
            category=record.category,
            team=record.team,
            project=record.project,
            member=record.member,
            roi_pct=record.roi_pct,
            audit_json=record.audit_json,
        )
        return record
    except Exception:
        logger.exception("Failed to persist business value record")
        return None


def build_executive_value_dashboard(*, board_id: str = "", days: int = 90) -> dict[str, Any]:
    """Executive value dashboard — all figures from BusinessValueRecordModel."""
    from django.db.models import Avg, Sum
    from django.utils import timezone
    from datetime import timedelta

    qs = BusinessValueRecordModel.objects.all()
    if board_id:
        qs = qs.filter(board_id=board_id)
    qs = qs.filter(created_at__gte=timezone.now() - timedelta(days=days))

    totals = qs.aggregate(
        value_created=Sum("realized_benefit"),
        losses_avoided=Sum("avoided_loss"),
        total_cost=Sum("estimated_cost"),
        avg_roi=Avg("roi_pct"),
        avg_confidence=Avg("confidence_score"),
    )

    return {
        "dashboard": "executive_value",
        "board_id": board_id or "all",
        "period_days": days,
        "summary": {
            "value_created_brl": round(totals["value_created"] or 0, 2),
            "losses_avoided_brl": round(totals["losses_avoided"] or 0, 2),
            "total_cost_brl": round(totals["total_cost"] or 0, 2),
            "avg_roi_pct": round(totals["avg_roi"] or 0, 1),
            "avg_confidence": round(totals["avg_confidence"] or 0, 2),
            "records": qs.count(),
        },
        "roi_by_action": aggregate_by_dimension("action", board_id=board_id, days=days),
        "roi_by_team": aggregate_by_dimension("team", board_id=board_id, days=days),
        "roi_by_project": aggregate_by_dimension("project", board_id=board_id, days=days),
        "waste_by_area": _waste_by_area(board_id, days),
        "trends": compute_value_trends(board_id=board_id, days=max(days, 365)),
        "narratives": _value_narratives(board_id, days),
    }


def _waste_by_area(board_id: str, days: int) -> list[dict[str, Any]]:
    """Areas with highest estimated cost (waste) — from operational cost records."""
    areas = aggregate_by_dimension("area", board_id=board_id, days=days)
    return sorted(areas, key=lambda x: x["estimated_cost"], reverse=True)[:10]


def _value_narratives(board_id: str, days: int) -> list[str]:
    from django.db.models import Avg, Count, Sum
    from django.utils import timezone
    from datetime import timedelta

    qs = BusinessValueRecordModel.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=days),
    )
    if board_id:
        qs = qs.filter(board_id=board_id)

    narratives = []
    by_action = qs.values("action_type").annotate(
        avoided=Sum("avoided_loss"),
        avg_roi=Avg("roi_pct"),
        count=Count("id"),
    ).order_by("-avoided")

    for row in by_action[:3]:
        if row["count"] and row["count"] > 0:
            narratives.append(
                f"Action {row['action_type']} avoided estimated losses of R$ {row['avoided']:,.2f} "
                f"in the last {days} days, with average ROI of {row['avg_roi'] or 0:.1f}% "
                f"({int(row['count'])} records, confidence-weighted)."
            )
    if not narratives:
        narratives.append("Insufficient value records for evidence-based financial narratives.")
    return narratives
