from __future__ import annotations

from typing import Any

from apps.intelligence.services.decision_layer.action_generator import generate_decisions_from_output
from apps.intelligence.services.decision_layer.prioritizer import build_action_queue, prioritize_decisions
from apps.intelligence.services.decision_layer.queue.manager import enqueue_decision


def enrich_with_decisions(
    output: dict[str, Any],
    *,
    source_trace_id: str = "",
    owner: str = "system",
    persist: bool = False,
) -> dict[str, Any]:
    """
    DAL integration hook — generate decision proposals from pipeline output.
    Does NOT auto-execute actions (insight ≠ action by default).
    """
    decisions = generate_decisions_from_output(output, source_trace_id=source_trace_id, owner=owner)
    ordered = prioritize_decisions(decisions)
    queue = build_action_queue(ordered)

    if persist:
        for d in ordered:
            enqueue_decision(d.to_dict())

    enriched = dict(output)
    enriched["decisions"] = [d.to_dict() for d in ordered]
    enriched["action_queue"] = queue
    enriched["decision_summary"] = {
        "total": len(ordered),
        "critical": sum(1 for d in ordered if d.priority == "CRITICAL"),
        "high": sum(1 for d in ordered if d.priority == "HIGH"),
        "auto_executable": sum(
            1 for q in queue if q["action"].get("execution_mode") == "AUTOMATIC"
        ),
    }
    return enriched
