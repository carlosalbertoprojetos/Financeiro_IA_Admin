from __future__ import annotations

from typing import Any

from apps.intelligence.services.report_query.domain.filters import (
    LabelOperator,
    MemberRole,
    PeriodPreset,
    ReportQueryPayload,
    ReportTemplate,
    SortField,
    SortOrder,
    StatusOperator,
)
from apps.intelligence.services.report_query.domain.query_options import GroupByField, ReportMetric
from apps.intelligence.services.risk_engine.scorer import assess_board_risk, assess_card_risk
from apps.intelligence.models import TimelineEvent
from integrations.trello.models import Card


REPORT_TYPE_MAP = {
    "EXECUTIVE": ReportTemplate.EXECUTIVO,
    "OPERATIONAL": ReportTemplate.OPERACIONAL,
    "MEMBER": ReportTemplate.MEMBRO,
    "LABEL": ReportTemplate.ETIQUETA,
    "PROJECT": ReportTemplate.PREFIXO,
}

METRIC_MAP = {
    "LEAD_TIME": ReportMetric.LEAD_TIME,
    "CYCLE_TIME": ReportMetric.CYCLE_TIME,
    "RISK_SCORE": ReportMetric.RISK_SCORE,
    "SLA": ReportMetric.SLA,
    "THROUGHPUT": ReportMetric.THROUGHPUT,
    "WIP": ReportMetric.WIP,
}

GROUP_MAP = {
    "LABELS": GroupByField.LABELS,
    "MEMBERS": GroupByField.MEMBERS,
    "STATUS": GroupByField.STATUS,
    "PREFIX": GroupByField.PREFIX,
    "LIST": GroupByField.LIST,
}

SORT_MAP = {
    "RISK_SCORE": SortField.RISK_SCORE,
    "LEAD_TIME": SortField.LEAD_TIME,
    "CYCLE_TIME": SortField.CYCLE_TIME,
    "TITLE": SortField.TITLE,
    "DUE_DATE": SortField.DUE_DATE,
}

PERIOD_EQL_MAP = {
    "LAST_7_DAYS": PeriodPreset.LAST_7_DAYS,
    "LAST_15_DAYS": PeriodPreset.LAST_15_DAYS,
    "LAST_30_DAYS": PeriodPreset.LAST_30_DAYS,
    "LAST_90_DAYS": PeriodPreset.LAST_90_DAYS,
    "TODAY": PeriodPreset.TODAY,
    "YESTERDAY": PeriodPreset.YESTERDAY,
    "THIS_MONTH": PeriodPreset.THIS_MONTH,
    "PREVIOUS_MONTH": PeriodPreset.PREVIOUS_MONTH,
    "QUARTER": PeriodPreset.QUARTER,
    "SEMESTER": PeriodPreset.SEMESTER,
    "YEAR": PeriodPreset.YEAR,
}


def ast_to_payload(query_ast: dict[str, Any]) -> ReportQueryPayload:
    """Convert validated EQL AST dict to ReportQueryPayload for execution."""
    filters = query_ast.get("filters", {})
    period_raw = filters.get("period", {})
    preset = None
    date_from = None
    date_to = None
    if isinstance(period_raw, dict):
        p = period_raw.get("preset", "")
        if p == "CUSTOM":
            date_from = period_raw.get("from")
            date_to = period_raw.get("to")
        elif p:
            preset = PERIOD_EQL_MAP.get(p, PeriodPreset.LAST_30_DAYS)

    labels_spec = filters.get("labels", {})
    members_spec = filters.get("members", {})
    status_spec = filters.get("status", {})

    sort_list = query_ast.get("sort", [{"field": "RISK_SCORE", "order": "DESC"}])
    sort0 = sort_list[0] if sort_list else {"field": "RISK_SCORE", "order": "DESC"}

    report_type = REPORT_TYPE_MAP.get(query_ast.get("type", "EXECUTIVE"), ReportTemplate.EXECUTIVO)

    return ReportQueryPayload(
        board_id=query_ast.get("board_id", ""),
        period=preset,
        date_from=date_from,
        date_to=date_to,
        title_prefix=filters.get("title_prefix", ""),
        labels=list(labels_spec.get("values", [])) if labels_spec else [],
        label_operator=LabelOperator(labels_spec.get("operator", "AND").lower()),
        members=list(members_spec.get("values", [])) if members_spec else [],
        member_role=MemberRole.ASSIGNEE,
        status=list(status_spec.get("values", [])) if status_spec else [],
        status_operator=StatusOperator(status_spec.get("operator", "OR").lower()),
        report_type=report_type,
        metrics=[METRIC_MAP[m] for m in query_ast.get("metrics", []) if m in METRIC_MAP],
        group_by=[GROUP_MAP[g] for g in query_ast.get("group_by", []) if g in GROUP_MAP],
        sort_by=SORT_MAP.get(sort0.get("field", "RISK_SCORE"), SortField.RISK_SCORE),
        sort_order=SortOrder(sort0.get("order", "DESC")),
        limit=query_ast.get("limit", 100),
        use_cache=False,
    )


def apply_risk_score_filter(cards: list[Card], spec: dict[str, Any]) -> list[Card]:
    op = spec.get("op", ">=")
    threshold = float(spec.get("value", 0))
    return [card for card in cards if _compare(assess_card_risk(card).score, op, threshold)]


def _compare(value: float, op: str, threshold: float) -> bool:
    if op == ">=":
        return value >= threshold
    if op == "<=":
        return value <= threshold
    if op == ">":
        return value > threshold
    if op == "<":
        return value < threshold
    return value == threshold


def fetch_timeline_summary(board_id: str, limit: int = 50) -> list[dict[str, Any]]:
    events = TimelineEvent.objects.filter(board__trello_id=board_id).order_by("-event_timestamp")[:limit]
    return [
        {
            "event_type": e.event_type,
            "timestamp": e.event_timestamp.isoformat(),
            "actor": e.actor,
            "card_id": e.card.trello_id if e.card else None,
        }
        for e in events
    ]


def build_standard_output(
    *,
    query_ast: dict[str, Any],
    cards: list[Card],
    card_rows: list[dict[str, Any]],
    metrics_summary: dict[str, Any],
    grouped: dict[str, Any],
    processing_ms: int,
) -> dict[str, Any]:
    board_id = query_ast.get("board_id", "")
    risks = assess_board_risk(board_trello_id=board_id) if cards else {"assessments": []}

    recommendations: list[str] = []
    if metrics_summary.get("sla", {}).get("compliance_pct") is not None:
        pct = metrics_summary["sla"]["compliance_pct"]
        if pct < 80:
            recommendations.append(f"SLA compliance at {pct}% — review overdue cards")
    if risks.get("high_risk_count", 0) > 0:
        recommendations.append(f"{risks['high_risk_count']} high-risk cards require attention")

    return {
        "summary": {
            "report_type": query_ast.get("type"),
            "board_id": board_id,
            "matched_cards": len(cards),
            "returned_cards": len(card_rows),
            "processing_ms": processing_ms,
            "limit": query_ast.get("limit", 100),
        },
        "metrics": metrics_summary,
        "grouped_data": grouped,
        "risks": {
            "high_risk_count": risks.get("high_risk_count", 0),
            "average_score": risks.get("average_score", 0),
            "top_assessments": risks.get("assessments", [])[:10],
        },
        "timeline": {"events": fetch_timeline_summary(board_id, limit=30)},
        "recommendations": recommendations,
        "cards": card_rows,
    }
