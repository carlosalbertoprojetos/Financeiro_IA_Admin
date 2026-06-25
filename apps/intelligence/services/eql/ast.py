from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class SortSpec:
    field: str
    order: Literal["ASC", "DESC"] = "DESC"


@dataclass
class ListFilter:
    values: list[str] = field(default_factory=list)
    operator: Literal["AND", "OR"] = "AND"


@dataclass
class ComparisonFilter:
    field: str
    op: str
    value: float | int | str


@dataclass
class EQLQuery:
    type: str = "EXECUTIVE"
    board_id: str = ""
    filters: dict[str, Any] = field(default_factory=dict)
    metrics: list[str] = field(default_factory=lambda: ["LEAD_TIME", "CYCLE_TIME", "RISK_SCORE", "SLA"])
    group_by: list[str] = field(default_factory=list)
    sort: list[SortSpec] = field(default_factory=lambda: [SortSpec("RISK_SCORE", "DESC")])
    limit: int = 100

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "board_id": self.board_id,
            "filters": self.filters,
            "metrics": self.metrics,
            "group_by": self.group_by,
            "sort": [{"field": s.field, "order": s.order} for s in self.sort],
            "limit": self.limit,
        }
