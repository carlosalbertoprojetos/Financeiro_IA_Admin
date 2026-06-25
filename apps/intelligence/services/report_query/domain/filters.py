from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PeriodPreset(str, Enum):
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_15_DAYS = "last_15_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    THIS_MONTH = "this_month"
    PREVIOUS_MONTH = "previous_month"
    QUARTER = "quarter"
    SEMESTER = "semester"
    YEAR = "year"
    CUSTOM = "custom"


class TitleMatchMode(str, Enum):
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"


class LabelOperator(str, Enum):
    AND = "and"
    OR = "or"


class MemberRole(str, Enum):
    ASSIGNEE = "assignee"
    PARTICIPANT = "participant"
    CREATOR = "creator"
    LAST_EDITOR = "last_editor"
    COMMENTER = "commenter"
    EXECUTOR = "executor"


class CardStatusFilter(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REOPENED = "reopened"


class PriorityFilter(str, Enum):
    LOW = "baixa"
    MEDIUM = "media"
    HIGH = "alta"
    CRITICAL = "critica"


class ChecklistFilter(str, Enum):
    WITH_CHECKLIST = "with_checklist"
    WITHOUT_CHECKLIST = "without_checklist"
    COMPLETED = "checklist_completed"
    PENDING = "checklist_pending"
    BLOCKED = "checklist_blocked"


class RiskLevelFilter(str, Enum):
    LOW = "baixo"
    MODERATE = "moderado"
    HIGH = "alto"
    CRITICAL = "critico"


class ReportTemplate(str, Enum):
    EXECUTIVO = "EXECUTIVO"
    OPERACIONAL = "OPERACIONAL"
    MEMBRO = "MEMBRO"
    EQUIPE = "EQUIPE"
    ETIQUETA = "ETIQUETA"
    PROJETO = "PROJETO"
    CLIENTE = "CLIENTE"
    RISCOS = "RISCOS"
    SLA = "SLA"
    PRODUTIVIDADE = "PRODUTIVIDADE"
    PREFIXO = "PREFIXO"
    MULTIDIMENSIONAL = "MULTIDIMENSIONAL"


from apps.intelligence.services.report_query.domain.query_options import (
    GroupByField,
    ReportMetric,
    SortField,
    SortOrder,
    StatusOperator,
)


class ExportFormat(str, Enum):
    JSON = "json"
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    MARKDOWN = "markdown"
    PPTX = "pptx"


@dataclass
class TitleFilter:
    mode: TitleMatchMode = TitleMatchMode.CONTAINS
    value: str = ""
    prefix: str = ""


@dataclass
class LabelFilter:
    values: list[str] = field(default_factory=list)
    operator: LabelOperator = LabelOperator.AND


@dataclass
class MemberFilter:
    values: list[str] = field(default_factory=list)
    role: MemberRole = MemberRole.ASSIGNEE


@dataclass
class ScoreRange:
    min_score: int = 0
    max_score: int = 100


@dataclass
class ReportQueryPayload:
    board_id: str
    period: PeriodPreset | None = None
    date_from: str | None = None
    date_to: str | None = None
    title_contains: str = ""
    title_filter: TitleFilter | None = None
    title_prefix: str = ""
    labels: list[str] = field(default_factory=list)
    label_operator: LabelOperator = LabelOperator.AND
    members: list[str] = field(default_factory=list)
    member_role: MemberRole = MemberRole.ASSIGNEE
    lists: list[str] = field(default_factory=list)
    status: list[str] = field(default_factory=list)
    priority: list[str] = field(default_factory=list)
    checklist: ChecklistFilter | None = None
    risk_levels: list[str] = field(default_factory=list)
    score_range: ScoreRange | None = None
    report_type: ReportTemplate = ReportTemplate.EXECUTIVO
    export_format: ExportFormat = ExportFormat.JSON
    metrics: list[ReportMetric] = field(default_factory=lambda: [
        ReportMetric.LEAD_TIME,
        ReportMetric.CYCLE_TIME,
        ReportMetric.RISK_SCORE,
        ReportMetric.SLA,
    ])
    group_by: list[GroupByField] = field(default_factory=list)
    sort_by: SortField = SortField.RISK_SCORE
    sort_order: SortOrder = SortOrder.DESC
    limit: int = 100
    status_operator: StatusOperator = StatusOperator.OR
    use_cache: bool = True
    generated_by: str = "anonymous"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReportQueryPayload:
        title_data = data.get("title_filter") or {}
        score_data = data.get("score_range") or {}

        title_filter = None
        if title_data or data.get("title_contains") or data.get("title_prefix"):
            title_filter = TitleFilter(
                mode=TitleMatchMode(title_data.get("mode", "contains")),
                value=title_data.get("value") or data.get("title_contains", ""),
                prefix=title_data.get("prefix") or data.get("title_prefix", ""),
            )

        score_range = None
        if score_data:
            score_range = ScoreRange(
                min_score=int(score_data.get("min", 0)),
                max_score=int(score_data.get("max", 100)),
            )

        checklist_raw = data.get("checklist")
        checklist = ChecklistFilter(checklist_raw) if checklist_raw else None

        period_raw = data.get("period")
        period = PeriodPreset(period_raw) if period_raw else None

        report_raw = data.get("report_type", "EXECUTIVO")
        export_raw = data.get("export_format", "json")

        metrics_raw = data.get("metrics") or []
        metrics = [ReportMetric(m.upper()) for m in metrics_raw] if metrics_raw else [
            ReportMetric.LEAD_TIME,
            ReportMetric.CYCLE_TIME,
            ReportMetric.RISK_SCORE,
            ReportMetric.SLA,
        ]

        group_raw = data.get("group_by") or []
        group_by = [GroupByField(g.upper()) for g in group_raw]

        sort_by = SortField(str(data.get("sort_by", "RISK_SCORE")).upper())
        sort_order = SortOrder(str(data.get("sort_order", "DESC")).upper())
        status_op = StatusOperator(str(data.get("status_operator", "or")).lower())

        title_prefix = str(data.get("title_prefix", "")).strip("[]")

        return cls(
            board_id=str(data.get("board_id", "")),
            period=period,
            date_from=data.get("date_from"),
            date_to=data.get("date_to"),
            title_contains=str(data.get("title_contains", "")),
            title_filter=title_filter,
            title_prefix=title_prefix,
            labels=list(data.get("labels") or []),
            label_operator=LabelOperator(data.get("label_operator", "and")),
            members=list(data.get("members") or []),
            member_role=MemberRole(data.get("member_role", "assignee")),
            lists=list(data.get("lists") or []),
            status=[s.lower() for s in (data.get("status") or [])],
            status_operator=status_op,
            priority=[p.lower() for p in (data.get("priority") or [])],
            checklist=checklist,
            risk_levels=[r.lower() for r in (data.get("risk_levels") or [])],
            score_range=score_range,
            report_type=ReportTemplate(report_raw),
            export_format=ExportFormat(export_raw),
            metrics=metrics,
            group_by=group_by,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=int(data.get("limit", 100)),
            use_cache=data.get("use_cache", True),
            generated_by=str(data.get("generated_by", "anonymous")),
        )

    def to_cache_key_dict(self) -> dict[str, Any]:
        return {
            "board_id": self.board_id,
            "period": self.period.value if self.period else None,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "title_contains": self.title_contains,
            "title_prefix": self.title_prefix,
            "labels": self.labels,
            "label_operator": self.label_operator.value,
            "members": self.members,
            "member_role": self.member_role.value,
            "lists": self.lists,
            "status": self.status,
            "status_operator": self.status_operator.value,
            "priority": self.priority,
            "checklist": self.checklist.value if self.checklist else None,
            "risk_levels": self.risk_levels,
            "score_range": {
                "min": self.score_range.min_score,
                "max": self.score_range.max_score,
            }
            if self.score_range
            else None,
            "report_type": self.report_type.value,
            "export_format": self.export_format.value,
            "metrics": [m.value for m in self.metrics],
            "group_by": [g.value for g in self.group_by],
            "sort_by": self.sort_by.value,
            "sort_order": self.sort_order.value,
            "limit": self.limit,
        }
