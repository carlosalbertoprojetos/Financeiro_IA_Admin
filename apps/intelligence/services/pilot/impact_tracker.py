from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from django.utils import timezone

from apps.intelligence.models import ActionImpactFollowUp, ActionExecutionLog, BusinessValueRecordModel
from apps.intelligence.services.business_value.pipeline import record_action_value
from apps.intelligence.services.decision_layer.feedback.loop import measure_action_impact
from apps.intelligence.services.decision_layer.orchestrator import _capture_card_state
from apps.intelligence.services.organizational_learning.pipeline import record_action_learning

logger = logging.getLogger(__name__)

FOLLOWUP_WINDOWS_HOURS = (24, 72, 168)


def schedule_impact_followups(
    *,
    decision_id: str,
    action_type: str,
    board_id: str = "",
    card_id: str = "",
    baseline: dict[str, Any] | None = None,
    execution_log_id: int | None = None,
) -> list[ActionImpactFollowUp]:
    """Schedule observed impact measurements — no inference, real card state at T+24h/72h/7d."""
    now = timezone.now()
    baseline = baseline or {}
    created: list[ActionImpactFollowUp] = []

    for hours in FOLLOWUP_WINDOWS_HOURS:
        followup, was_created = ActionImpactFollowUp.objects.get_or_create(
            decision_id=decision_id,
            window_hours=hours,
            defaults={
                "execution_log_id": execution_log_id,
                "board_id": board_id,
                "card_id": card_id,
                "action_type": action_type,
                "scheduled_at": now + timedelta(hours=hours),
                "baseline_json": baseline,
                "status": ActionImpactFollowUp.Status.SCHEDULED,
            },
        )
        if was_created:
            created.append(followup)
    return created


def process_due_followups(*, board_id: str = "", limit: int = 50) -> dict[str, Any]:
    """Measure all follow-ups whose scheduled time has passed."""
    now = timezone.now()
    qs = ActionImpactFollowUp.objects.filter(
        status=ActionImpactFollowUp.Status.SCHEDULED,
        scheduled_at__lte=now,
    )
    if board_id:
        qs = qs.filter(board_id=board_id)
    results = {"measured": 0, "failed": 0, "details": []}
    for followup in qs.order_by("scheduled_at")[:limit]:
        detail = measure_followup(followup.id)
        results["details"].append(detail)
        if detail.get("status") == "MEASURED":
            results["measured"] += 1
        else:
            results["failed"] += 1
    return results


def measure_followup(followup_id: int) -> dict[str, Any]:
    """Re-capture card state and compare to baseline — real observed impact."""
    followup = ActionImpactFollowUp.objects.filter(id=followup_id).first()
    if not followup:
        return {"status": "NOT_FOUND", "followup_id": followup_id}

    if followup.status != ActionImpactFollowUp.Status.SCHEDULED:
        return {"status": followup.status, "followup_id": followup_id}

    try:
        baseline = followup.baseline_json or {}
        measured = _capture_card_state(followup.card_id)
        impact = measure_action_impact(
            before=baseline,
            after=measured,
            action_type=followup.action_type,
        )

        estimated = _load_estimated_value(followup.decision_id)
        realized_avoided = max(0, (baseline.get("risk_score", 0) - measured.get("risk_score", 0)))
        estimated_avoided = estimated.get("avoided_loss", 0) if estimated else 0
        prediction_error_pct = 0.0
        if estimated_avoided:
            prediction_error_pct = round(
                abs(estimated_avoided - realized_avoided) / estimated_avoided * 100, 2,
            )

        evr = {
            "estimated_avoided_loss": estimated_avoided,
            "realized_risk_delta": realized_avoided,
            "prediction_error_pct": prediction_error_pct,
            "window_hours": followup.window_hours,
        }

        followup.measured_json = measured
        followup.impact_json = impact
        followup.estimated_vs_realized_json = evr
        followup.measured_at = timezone.now()
        followup.status = ActionImpactFollowUp.Status.MEASURED
        followup.save()

        record_action_learning(
            decision_id=followup.decision_id,
            action_type=followup.action_type,
            before=baseline,
            after=measured,
            impact=impact,
            execution_time_ms=followup.window_hours * 3600 * 1000,
            board_id=followup.board_id,
            category=f"followup_{followup.window_hours}h",
            owner="pocl_impact_tracker",
            context={"window_hours": followup.window_hours, "observed": True},
        )
        record_action_value(
            decision_id=f"{followup.decision_id}_followup_{followup.window_hours}h",
            action_type=followup.action_type,
            before=baseline,
            after=measured,
            board_id=followup.board_id,
            category=f"followup_{followup.window_hours}h",
            card_id=followup.card_id,
        )

        return {
            "status": "MEASURED",
            "followup_id": followup_id,
            "window_hours": followup.window_hours,
            "impact": impact,
            "estimated_vs_realized": evr,
        }
    except Exception as exc:
        logger.exception("Follow-up measurement failed: %s", followup_id)
        followup.status = ActionImpactFollowUp.Status.FAILED
        followup.measured_at = timezone.now()
        followup.impact_json = {"error": str(exc)}
        followup.save(update_fields=["status", "measured_at", "impact_json", "updated_at"])
        return {"status": "FAILED", "followup_id": followup_id, "error": str(exc)}


def _load_estimated_value(decision_id: str) -> dict[str, Any]:
    record = BusinessValueRecordModel.objects.filter(
        source_id=decision_id,
        source_type="action_execution",
    ).order_by("-created_at").first()
    if not record:
        return {}
    return {
        "avoided_loss": record.avoided_loss,
        "estimated_benefit": record.estimated_benefit,
        "realized_benefit": record.realized_benefit,
        "roi_pct": record.roi_pct,
    }
