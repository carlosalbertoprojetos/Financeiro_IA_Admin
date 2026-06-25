from __future__ import annotations

import logging
from typing import Any

from django.utils import timezone

from apps.intelligence.models import PilotCycleRun
from apps.intelligence.services.pilot.config import ensure_human_in_loop, get_active_pilot
from apps.intelligence.services.pilot.decision_stream import run_decision_stream
from apps.intelligence.services.pilot.impact_tracker import process_due_followups
from apps.intelligence.services.pilot.report_generator import generate_executive_daily_report

logger = logging.getLogger(__name__)


def run_daily_cycle(
    board_id: str,
    *,
    phase: str = "morning",
    trigger: str = "scheduled",
    sync: bool = True,
) -> dict[str, Any]:
    """
    Daily operational cycle:
    - morning: sync + backlog/risk analysis + prioritization suggestions
    - intraday: sync + change detection + intervention suggestions
    - eod: decision summary + impact follow-ups + executive report
    """
    ensure_human_in_loop()
    pilot = get_active_pilot(board_id=board_id)
    if not pilot:
        return {"status": "NO_ACTIVE_PILOT", "board_id": board_id}

    phase_upper = phase.upper()
    valid_phases = {choice.value for choice in PilotCycleRun.Phase}
    if phase_upper not in valid_phases:
        phase_upper = PilotCycleRun.Phase.MORNING

    cycle = PilotCycleRun.objects.create(
        pilot=pilot,
        board_id=board_id,
        phase=phase_upper,
        trigger=trigger,
        status="RUNNING",
    )
    summary: dict[str, Any] = {
        "board_id": board_id,
        "phase": phase_upper,
        "trigger": trigger,
        "started_at": timezone.now().isoformat(),
    }

    try:
        if sync and phase_upper in (PilotCycleRun.Phase.MORNING, PilotCycleRun.Phase.INTRADAY):
            from integrations.trello.services.sync import sync_board

            sync_result = sync_board(board_id)
            summary["sync"] = sync_result.as_dict()

        if phase_upper == PilotCycleRun.Phase.MORNING:
            summary["decision_stream"] = run_decision_stream(
                board_id, trigger=f"daily_{phase}", limit=25, query_template="executive",
            )
        elif phase_upper == PilotCycleRun.Phase.INTRADAY:
            summary["decision_stream"] = run_decision_stream(
                board_id, trigger=f"daily_{phase}", limit=15, query_template="risk",
            )
        elif phase_upper == PilotCycleRun.Phase.EOD:
            summary["impact_followups"] = process_due_followups(board_id=board_id)
            report_path = generate_executive_daily_report(board_id=board_id, pilot=pilot)
            summary["executive_report"] = report_path
            summary["decision_stream"] = run_decision_stream(
                board_id, trigger=f"daily_{phase}", limit=10, query_template="executive",
            )

        summary["status"] = "COMPLETED"
        cycle.summary_json = summary
        cycle.status = "COMPLETED"
        cycle.completed_at = timezone.now()
        cycle.save(update_fields=["summary_json", "status", "completed_at", "updated_at"])
        return summary
    except Exception as exc:
        logger.exception("Daily cycle %s failed for board %s", phase_upper, board_id)
        summary.update({"status": "FAILED", "error": str(exc)})
        cycle.summary_json = summary
        cycle.status = "FAILED"
        cycle.completed_at = timezone.now()
        cycle.save(update_fields=["summary_json", "status", "completed_at", "updated_at"])
        return summary
