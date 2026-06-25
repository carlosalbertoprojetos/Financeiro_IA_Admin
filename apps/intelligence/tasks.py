import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="intelligence.pocl_decision_stream")
def pocl_decision_stream_task(board_id: str, trigger: str = "scheduled") -> dict:
    from apps.intelligence.services.pilot.decision_stream import run_decision_stream

    return run_decision_stream(board_id, trigger=trigger, limit=15)


@shared_task(name="intelligence.pocl_daily_cycle")
def pocl_daily_cycle_task(board_id: str, phase: str = "morning") -> dict:
    from apps.intelligence.services.pilot.daily_cycle import run_daily_cycle

    sync = phase in ("morning", "intraday")
    return run_daily_cycle(board_id, phase=phase, trigger="celery", sync=sync)


@shared_task(name="intelligence.pocl_measure_followups")
def pocl_measure_followups_task(board_id: str = "") -> dict:
    from apps.intelligence.services.pilot.impact_tracker import process_due_followups

    return process_due_followups(board_id=board_id)
