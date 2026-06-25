from __future__ import annotations

import logging
from typing import Any

from django.utils import timezone

from apps.intelligence.models import PilotCycleRun
from apps.intelligence.services.decision_layer.pipeline import enrich_with_decisions
from apps.intelligence.services.pilot.config import ensure_human_in_loop, get_active_pilot
from apps.intelligence.services.query_engine.runner import execute_eql_query

logger = logging.getLogger(__name__)

EXECUTIVE_EQL = """REPORT:
TYPE = EXECUTIVE
FILTER:
PERIOD = LAST_30_DAYS
LIMIT:
{limit}
"""

RISK_EQL = """REPORT:
TYPE = EXECUTIVE
FILTER:
PERIOD = LAST_7_DAYS
RISK_LEVEL >= HIGH
LIMIT:
{limit}
"""


def run_decision_stream(
    board_id: str,
    *,
    trigger: str = "manual",
    limit: int = 20,
    query_template: str = "executive",
    user_id: str = "pocl",
) -> dict[str, Any]:
    """
    Continuous decision stream: sync data → EQL → semantic → DAL proposals → persist queue.
    Never auto-executes — human-in-the-loop only.
    """
    ensure_human_in_loop()
    pilot = get_active_pilot(board_id=board_id)
    cycle = None
    if pilot:
        cycle = PilotCycleRun.objects.create(
            pilot=pilot,
            board_id=board_id,
            phase=PilotCycleRun.Phase.STREAM,
            trigger=trigger,
            status="RUNNING",
        )

    query_text = (EXECUTIVE_EQL if query_template == "executive" else RISK_EQL).format(limit=limit)
    summary: dict[str, Any] = {
        "board_id": board_id,
        "trigger": trigger,
        "query_template": query_template,
        "started_at": timezone.now().isoformat(),
    }

    try:
        result = execute_eql_query(
            query_text,
            board_id=board_id,
            user_id=user_id,
            use_cache=False,
            timeout_ms=180_000,
        )
        trace_id = result.get("trace_id", "")
        output = dict(result)
        enriched = enrich_with_decisions(
            output,
            source_trace_id=trace_id,
            owner=user_id,
            persist=True,
        )
        summary.update({
            "trace_id": trace_id,
            "matched_cards": result.get("summary", {}).get("matched_cards", 0),
            "decisions_generated": enriched.get("decision_summary", {}).get("total", 0),
            "critical_decisions": enriched.get("decision_summary", {}).get("critical", 0),
            "high_decisions": enriched.get("decision_summary", {}).get("high", 0),
            "decisions_persisted": True,
            "status": "OK",
        })
        if cycle:
            cycle.trace_id = trace_id
            cycle.summary_json = summary
            cycle.status = "COMPLETED"
            cycle.completed_at = timezone.now()
            cycle.save(update_fields=["trace_id", "summary_json", "status", "completed_at", "updated_at"])
        return summary
    except Exception as exc:
        logger.exception("Decision stream failed for board %s", board_id)
        summary.update({"status": "FAILED", "error": str(exc)})
        if cycle:
            cycle.summary_json = summary
            cycle.status = "FAILED"
            cycle.completed_at = timezone.now()
            cycle.save(update_fields=["summary_json", "status", "completed_at", "updated_at"])
        return summary
