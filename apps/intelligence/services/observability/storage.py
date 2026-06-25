from __future__ import annotations

import logging
from typing import Any

from apps.intelligence.models import DecisionTraceRecord
from apps.intelligence.services.observability.trace.model import DecisionTrace

logger = logging.getLogger(__name__)


def persist_trace(trace: DecisionTrace, *, query_raw: str, board_id: str = "", user_id: str = "anonymous") -> str:
    """Persist decision trace to database."""
    try:
        summary = {
            "matched_cards": trace.final_output_summary.get("matched_cards", 0),
            "entities": trace.final_output_summary.get("entities_count", 0),
            "steps": len(trace.steps),
            "errors": len(trace.errors),
        }
        DecisionTraceRecord.objects.create(
            trace_id=trace.trace_id,
            query_id=trace.query_id,
            query=query_raw[:10000],
            board_id=board_id,
            user_id=user_id,
            execution_time_ms=trace.execution_time_ms,
            status=trace.status,
            summary=summary,
            full_trace_json=trace.to_dict(),
        )
    except Exception:
        logger.exception("Failed to persist decision trace")
    return trace.trace_id


def load_trace(trace_id: str) -> dict[str, Any] | None:
    row = DecisionTraceRecord.objects.filter(trace_id=trace_id).first()
    return row.full_trace_json if row else None


def load_traces_by_query_id(query_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
    rows = DecisionTraceRecord.objects.filter(query_id=query_id).order_by("-created_at")[:limit]
    return [r.full_trace_json for r in rows]
