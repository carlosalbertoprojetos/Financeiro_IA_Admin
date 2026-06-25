from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from django.utils import timezone

from analytics.adapters import card_to_record
from analytics.engine import metrics as metric_engine
from apps.intelligence.services.report_query.domain.filters import ReportQueryPayload
from apps.intelligence.services.report_query.domain.query_options import (
    GroupByField,
    ReportMetric,
    SortField,
    SortOrder,
)
from apps.intelligence.services.report_query.domain.title_parser import extract_prefix
from apps.intelligence.services.report_query.engine.card_metrics import get_card_label_names
from apps.intelligence.services.risk_engine.scorer import assess_card_risk
from integrations.trello.models import Card


def build_card_rows(cards: list[Card], payload: ReportQueryPayload) -> list[dict[str, Any]]:
    """Enrich cards with requested metrics, sort and limit."""
    rows: list[dict[str, Any]] = []
    now = timezone.now()

    for card in cards:
        row = _card_base_row(card)
        if ReportMetric.LEAD_TIME in payload.metrics or payload.sort_by == SortField.LEAD_TIME:
            row["lead_time_hours"] = _card_lead_time_hours(card)
        if ReportMetric.CYCLE_TIME in payload.metrics or payload.sort_by == SortField.CYCLE_TIME:
            row["cycle_time_hours"] = _card_cycle_time_hours(card)
        if ReportMetric.RISK_SCORE in payload.metrics or payload.sort_by == SortField.RISK_SCORE:
            risk = assess_card_risk(card)
            row["risk_score"] = risk.score
            row["risk_level"] = risk.level
        if ReportMetric.SLA in payload.metrics:
            row["sla"] = _card_sla(card, now)
        rows.append(row)

    rows = _sort_rows(rows, payload.sort_by, payload.sort_order)
    if payload.limit:
        rows = rows[: payload.limit]
    return rows


def build_grouped_summary(rows: list[dict[str, Any]], group_by: list[GroupByField]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    if GroupByField.LABELS in group_by:
        summary["by_labels"] = _group_by_labels(rows)
    if GroupByField.MEMBERS in group_by:
        summary["by_members"] = _group_by_field(rows, "assignees")
    if GroupByField.STATUS in group_by:
        summary["by_status"] = _group_by_field(rows, "status")
    if GroupByField.PREFIX in group_by:
        summary["by_prefix"] = _group_by_field(rows, "prefix")
    return summary


def build_metrics_summary(rows: list[dict[str, Any]], metrics: list[ReportMetric]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if ReportMetric.LEAD_TIME in metrics:
        values = [r["lead_time_hours"] for r in rows if r.get("lead_time_hours") is not None]
        result["lead_time"] = _numeric_summary(values)
    if ReportMetric.CYCLE_TIME in metrics:
        values = [r["cycle_time_hours"] for r in rows if r.get("cycle_time_hours") is not None]
        result["cycle_time"] = _numeric_summary(values)
    if ReportMetric.RISK_SCORE in metrics:
        values = [r["risk_score"] for r in rows if r.get("risk_score") is not None]
        result["risk_score"] = _numeric_summary(values)
    if ReportMetric.SLA in metrics:
        sla_rows = [r["sla"] for r in rows if r.get("sla")]
        on_time = sum(1 for s in sla_rows if s == "No prazo" or s == "Cumprido")
        result["sla"] = {
            "total": len(sla_rows),
            "on_time": on_time,
            "compliance_pct": round(on_time / len(sla_rows) * 100, 1) if sla_rows else None,
        }
    return result


def _card_base_row(card: Card) -> dict[str, Any]:
    assignees = [m.full_name or m.username or m.trello_id for m in card.assignees.all()]
    return {
        "card_id": card.trello_id,
        "title": card.title,
        "status": card.status,
        "labels": get_card_label_names(card),
        "assignees": assignees,
        "prefix": extract_prefix(card.title) or "",
        "due_at": card.due_at.isoformat() if card.due_at else None,
        "completed_at": card.completed_at.isoformat() if card.completed_at else None,
    }


def _card_lead_time_hours(card: Card) -> float | None:
    record = card_to_record(card)
    items = metric_engine.lead_time([record]).get("items", [])
    return items[0]["lead_time_hours"] if items else None


def _card_cycle_time_hours(card: Card) -> float | None:
    record = card_to_record(card)
    items = metric_engine.cycle_time([record]).get("items", [])
    return items[0]["cycle_time_hours"] if items else None


def _card_sla(card: Card, now: datetime) -> str:
    if not card.due_at:
        return "N/A"
    if card.completed_at:
        return "Cumprido" if card.completed_at <= card.due_at else "Violado"
    if card.due_at < now:
        return "Violado"
    if (card.due_at - now).days <= 2:
        return "Em risco"
    return "No prazo"


def _sort_rows(rows: list[dict[str, Any]], sort_by: SortField, order: SortOrder) -> list[dict[str, Any]]:
    key_map = {
        SortField.RISK_SCORE: lambda r: r.get("risk_score", 0),
        SortField.LEAD_TIME: lambda r: r.get("lead_time_hours") or 0,
        SortField.CYCLE_TIME: lambda r: r.get("cycle_time_hours") or 0,
        SortField.TITLE: lambda r: r.get("title", "").lower(),
        SortField.DUE_DATE: lambda r: r.get("due_at") or "",
    }
    key_fn = key_map.get(sort_by, key_map[SortField.RISK_SCORE])
    return sorted(rows, key=key_fn, reverse=order == SortOrder.DESC)


def _group_by_labels(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list] = defaultdict(list)
    for row in rows:
        labels = row.get("labels") or ["Sem etiqueta"]
        for label in labels:
            groups[label].append(row)
    return [_group_stats(name, items) for name, items in sorted(groups.items())]


def _group_by_field(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    groups: dict[str, list] = defaultdict(list)
    for row in rows:
        if field == "assignees":
            keys = row.get("assignees") or ["Não atribuído"]
            for key in keys:
                groups[key].append(row)
        else:
            groups[str(row.get(field) or "N/A")].append(row)
    return [_group_stats(name, items) for name, items in sorted(groups.items())]


def _group_stats(name: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    risk_values = [i.get("risk_score") for i in items if i.get("risk_score") is not None]
    return {
        "name": name,
        "count": len(items),
        "avg_risk_score": round(sum(risk_values) / len(risk_values), 1) if risk_values else None,
        "card_ids": [i["card_id"] for i in items[:20]],
    }


def _numeric_summary(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "avg": None, "min": None, "max": None}
    return {
        "count": len(values),
        "avg": round(sum(values) / len(values), 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
    }
