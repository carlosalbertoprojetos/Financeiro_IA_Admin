from __future__ import annotations

from apps.intelligence.services.report_query.domain.filters import CardStatusFilter

STATUS_ALIASES: dict[str, CardStatusFilter] = {
    "open": CardStatusFilter.OPEN,
    "aberto": CardStatusFilter.OPEN,
    "in_progress": CardStatusFilter.IN_PROGRESS,
    "em andamento": CardStatusFilter.IN_PROGRESS,
    "andamento": CardStatusFilter.IN_PROGRESS,
    "blocked": CardStatusFilter.BLOCKED,
    "bloqueado": CardStatusFilter.BLOCKED,
    "completed": CardStatusFilter.COMPLETED,
    "concluido": CardStatusFilter.COMPLETED,
    "concluído": CardStatusFilter.COMPLETED,
    "overdue": CardStatusFilter.OVERDUE,
    "atrasado": CardStatusFilter.OVERDUE,
    "cancelled": CardStatusFilter.CANCELLED,
    "cancelado": CardStatusFilter.CANCELLED,
    "reopened": CardStatusFilter.REOPENED,
    "reaberto": CardStatusFilter.REOPENED,
}


def resolve_status_filter(raw: str) -> CardStatusFilter | None:
    key = raw.lower().strip()
    if key in STATUS_ALIASES:
        return STATUS_ALIASES[key]
    try:
        return CardStatusFilter(key)
    except ValueError:
        return None
