from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class DecisionEffectiveness:
    decision_id: str
    action_type: str
    risk_before: float
    risk_after: float
    sla_before: float
    sla_after: float
    execution_time: int
    outcome_score: float
    effectiveness_score: float
    outcome_label: str = ""
    board_id: str = ""
    category: str = ""
    owner: str = ""
    context: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
