from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class BusinessValueRecord:
    source_id: str
    source_type: str
    value_type: str
    estimated_cost: float = 0.0
    estimated_benefit: float = 0.0
    realized_benefit: float = 0.0
    avoided_loss: float = 0.0
    confidence_score: float = 0.0
    currency: str = "BRL"
    board_id: str = ""
    action_type: str = ""
    category: str = ""
    team: str = ""
    project: str = ""
    member: str = ""
    roi_pct: float = 0.0
    audit_json: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
