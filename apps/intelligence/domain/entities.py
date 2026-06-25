from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class TimelineEntry:
    event_type: str
    event_timestamp: datetime
    actor: str
    description: str
    is_critical: bool = False
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CardContext:
    """Executive context extracted from card data."""

    card_id: str
    title: str
    objective: str = ""
    area: str = ""
    department: str = ""
    project: str = ""
    client: str = ""
    priority: str = "MÉDIA"
    urgency: str = "MÉDIA"
    complexity: str = "MÉDIA"
    impact: str = "MÉDIA"
    criticality: str = "MÉDIA"
    business_value: str = "MÉDIA"
    confidence: float = 0.0
    signals: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CommunicationAnalysis:
    card_id: str
    executive_summary: str
    decisions: tuple[str, ...] = field(default_factory=tuple)
    pending_items: tuple[str, ...] = field(default_factory=tuple)
    risks: tuple[str, ...] = field(default_factory=tuple)
    unanswered_requests: tuple[str, ...] = field(default_factory=tuple)
    external_dependencies: tuple[str, ...] = field(default_factory=tuple)
    escalations_needed: tuple[str, ...] = field(default_factory=tuple)
    comment_count: int = 0


@dataclass(frozen=True)
class ChecklistMetrics:
    card_id: str
    total_items: int = 0
    completed_items: int = 0
    pending_items: int = 0
    completion_pct: float = 0.0
    critical_pending: tuple[str, ...] = field(default_factory=tuple)
    blocked_items: tuple[str, ...] = field(default_factory=tuple)
    overdue_items: tuple[str, ...] = field(default_factory=tuple)
    never_started: tuple[str, ...] = field(default_factory=tuple)
    execution_score: float = 0.0


@dataclass(frozen=True)
class RiskAssessment:
    card_id: str
    score: int
    level: str
    factors: tuple[dict[str, Any], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PredictiveResult:
    card_id: str
    delay_probability: float
    block_probability: float
    estimated_completion: datetime | None
    escalation_needed: bool
    operational_risk: str
    sla_risk: str


@dataclass(frozen=True)
class OperationalScoreResult:
    board_id: str
    score: int
    level: str
    components: dict[str, int] = field(default_factory=dict)
