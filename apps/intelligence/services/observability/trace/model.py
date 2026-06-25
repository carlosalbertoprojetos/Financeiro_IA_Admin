from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TraceStep:
    name: str
    layer: str
    duration_ms: int = 0
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "layer": self.layer, "duration_ms": self.duration_ms, "details": self.details}


@dataclass
class DecisionTrace:
    trace_id: str
    query_id: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    inputs: list[dict[str, Any]] = field(default_factory=list)
    transformations: list[dict[str, Any]] = field(default_factory=list)
    semantic_mappings: list[dict[str, Any]] = field(default_factory=list)
    metrics_calculated: list[dict[str, Any]] = field(default_factory=list)
    rules_applied: list[dict[str, Any]] = field(default_factory=list)
    ai_decisions: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    query_lineage: dict[str, Any] = field(default_factory=dict)
    execution_path: list[dict[str, Any]] = field(default_factory=list)
    actions_taken: list[dict[str, Any]] = field(default_factory=list)
    final_output_summary: dict[str, Any] = field(default_factory=dict)
    status: str = "success"
    execution_time_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "query_id": self.query_id,
            "steps": self.steps,
            "inputs": self.inputs,
            "transformations": self.transformations,
            "semantic_mappings": self.semantic_mappings,
            "metrics_calculated": self.metrics_calculated,
            "rules_applied": self.rules_applied,
            "ai_decisions": self.ai_decisions,
            "errors": self.errors,
            "query_lineage": self.query_lineage,
            "execution_path": self.execution_path,
            "actions_taken": self.actions_taken,
            "final_output": self.final_output_summary,
            "status": self.status,
            "execution_time_ms": self.execution_time_ms,
        }
