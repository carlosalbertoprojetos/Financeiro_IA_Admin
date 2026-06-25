from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any

from apps.intelligence.services.observability.trace.model import DecisionTrace, TraceStep


def compute_query_id(query_text: str, board_id: str = "") -> str:
    """Deterministic ID for query lineage grouping (reproducibility)."""
    raw = json.dumps({"query": query_text.strip(), "board_id": board_id}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


class TraceCollector:
    """Collects decision trace data throughout the pipeline."""

    def __init__(self, *, query_text: str, board_id: str = "", user_id: str = "anonymous") -> None:
        self.query_text = query_text
        self.board_id = board_id
        self.user_id = user_id
        self.query_id = compute_query_id(query_text, board_id)
        self.trace_id = str(uuid.uuid4())
        self.trace = DecisionTrace(trace_id=self.trace_id, query_id=self.query_id)
        self._step_starts: dict[str, float] = {}

    def record_input(self, name: str, data: dict[str, Any]) -> None:
        self.trace.inputs.append({"name": name, "data": data})

    def start_step(self, name: str, layer: str) -> None:
        self._step_starts[name] = time.perf_counter()

    def end_step(self, name: str, layer: str, **details: Any) -> None:
        start = self._step_starts.pop(name, time.perf_counter())
        duration_ms = int((time.perf_counter() - start) * 1000)
        step = TraceStep(name=name, layer=layer, duration_ms=duration_ms, details=details)
        self.trace.steps.append(step.to_dict())
        self.trace.execution_path.append({"step": name, "layer": layer, "duration_ms": duration_ms})

    def record_transformation(self, name: str, before: str, after: str, **meta: Any) -> None:
        self.trace.transformations.append({
            "name": name,
            "before": before,
            "after": after,
            **meta,
        })

    def record_semantic_mapping(self, card_id: str, entity_type: str, rules: list[str], **meta: Any) -> None:
        self.trace.semantic_mappings.append({
            "card_id": card_id,
            "entity_type": entity_type,
            "rules_applied": rules,
            **meta,
        })

    def record_metric(self, name: str, value: Any, *, layer: str, formula: str, sources: list[str], model_version: str = "1.1") -> None:
        self.trace.metrics_calculated.append({
            "metric": name,
            "value": value,
            "layer": layer,
            "formula": formula,
            "event_sources": sources,
            "model_version": model_version,
        })

    def record_rule(self, rule: str, layer: str, effect: str, **meta: Any) -> None:
        self.trace.rules_applied.append({"rule": rule, "layer": layer, "effect": effect, **meta})

    def record_error(self, code: str, message: str, layer: str, **meta: Any) -> None:
        self.trace.errors.append({"code": code, "message": message, "layer": layer, **meta})
        self.trace.status = "error"

    def record_action(
        self,
        decision_id: str,
        action_type: str,
        trace_id: str,
        effect: str,
        meta: dict[str, Any],
    ) -> None:
        self.trace.actions_taken.append({
            "decision_id": decision_id,
            "action_type": action_type,
            "trace_id": trace_id,
            "effect": effect,
            **meta,
        })

    def set_query_lineage(self, lineage: dict[str, Any]) -> None:
        self.trace.query_lineage = lineage

    def finalize(self, output: dict[str, Any], *, execution_ms: int, status: str = "success") -> DecisionTrace:
        self.trace.status = status
        self.trace.execution_time_ms = execution_ms
        self.trace.final_output_summary = {
            "matched_cards": output.get("summary", {}).get("matched_cards", 0),
            "entities_count": len(output.get("entities", [])),
            "insights_count": len(output.get("domain_insights", [])),
            "governed": output.get("governance", {}).get("governed", True),
            "cache_hit": output.get("summary", {}).get("cache_hit", False),
        }
        return self.trace
