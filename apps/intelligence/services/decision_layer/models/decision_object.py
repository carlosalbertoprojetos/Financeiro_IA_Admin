from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class DecisionPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DecisionStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    PENDING_APPROVAL = "PENDING_APPROVAL"


class ExecutionMode(str, Enum):
    AUTOMATIC = "AUTOMATIC"
    SEMI_AUTOMATIC = "SEMI_AUTOMATIC"
    MANUAL = "MANUAL"


@dataclass
class RecommendedAction:
    action_type: str
    description: str
    execution_mode: str = ExecutionMode.MANUAL.value
    params: dict[str, Any] = field(default_factory=dict)
    target_card_id: str = ""
    target_board_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionObject:
    id: str = ""
    source_trace_id: str = ""
    insight: str = ""
    priority: str = DecisionPriority.MEDIUM.value
    recommended_actions: list[dict[str, Any]] = field(default_factory=list)
    status: str = DecisionStatus.OPEN.value
    owner: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    execution_history: list[dict[str, Any]] = field(default_factory=list)
    score: float = 0.0
    board_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def create(
        cls,
        *,
        insight: str,
        source_trace_id: str = "",
        priority: str = DecisionPriority.MEDIUM.value,
        recommended_actions: list[RecommendedAction] | None = None,
        owner: str = "",
        context: dict[str, Any] | None = None,
        board_id: str = "",
        score: float = 0.0,
    ) -> DecisionObject:
        actions = recommended_actions or []
        return cls(
            id=str(uuid4()),
            source_trace_id=source_trace_id,
            insight=insight,
            priority=priority,
            recommended_actions=[a.to_dict() if isinstance(a, RecommendedAction) else a for a in actions],
            status=DecisionStatus.OPEN.value,
            owner=owner,
            context=context or {},
            created_at=datetime.now(timezone.utc).isoformat(),
            execution_history=[],
            score=score,
            board_id=board_id,
        )
