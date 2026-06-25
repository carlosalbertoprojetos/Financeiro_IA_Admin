from __future__ import annotations

import re
from typing import Any

from apps.intelligence.services.report_query.domain.filters import (
    LabelOperator,
    PeriodPreset,
    ReportTemplate,
)

SECTION_PATTERN = re.compile(r"^(REPORT|TYPE|FILTER|METRICS|GROUP_BY|SORT|LIMIT)\s*:\s*(.*)$", re.I)
KV_PATTERN = re.compile(r"^([A-Z_]+)\s*=\s*(.+)$", re.I)
STATUS_OR_PATTERN = re.compile(r"\(([^)]+)\)", re.I)


def parse_report_dsl(text: str) -> dict[str, Any]:
    """
    Parse structured report DSL into API payload dict.

    Example::
        REPORT:
        TYPE = EXECUTIVE
        FILTER:
        PERIOD = LAST_30_DAYS
        ...
    """
    data: dict[str, Any] = {}
    current_section = ""

    for raw_line in text.strip().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        section_match = SECTION_PATTERN.match(line)
        if section_match:
            current_section = section_match.group(1).upper()
            remainder = section_match.group(2).strip()
            if remainder:
                _apply_line(data, current_section, remainder)
            continue

        _apply_line(data, current_section, line)

    return _normalize_payload(data)


def _apply_line(data: dict[str, Any], section: str, line: str) -> None:
    kv = KV_PATTERN.match(line)
    if not kv:
        if section == "METRICS":
            data.setdefault("metrics", []).extend(_split_csv(line))
        elif section == "GROUP_BY":
            data.setdefault("group_by", []).extend(_split_csv(line))
        return

    key = kv.group(1).upper()
    value = kv.group(2).strip()

    if section in ("REPORT", "TYPE", "") and key in ("TYPE", "REPORT_TYPE"):
        data["report_type"] = _map_report_type(value)
        return

    if section == "FILTER" or key in _FILTER_KEYS:
        _apply_filter(data, key, value)
        return

    if section == "METRICS" or key == "METRICS":
        data["metrics"] = _split_csv(value)
        return

    if section == "GROUP_BY" or key == "GROUP_BY":
        data["group_by"] = [g.strip().upper() for g in _split_csv(value)]
        return

    if section == "SORT" or key in ("SORT", "ORDER_BY"):
        field, order = _parse_sort(value)
        data["sort_by"] = field
        data["sort_order"] = order
        return

    if section == "LIMIT" or key == "LIMIT":
        data["limit"] = int(re.sub(r"\D", "", value) or "100")
        return


_FILTER_KEYS = frozenset(
    {
        "PERIOD",
        "LABELS",
        "MEMBERS",
        "TITLE_PREFIX",
        "STATUS",
        "LISTS",
        "PRIORITY",
        "RISK_LEVELS",
        "BOARD_ID",
    }
)


def _apply_filter(data: dict[str, Any], key: str, value: str) -> None:
    if key == "PERIOD":
        data["period"] = _map_period(value)
    elif key == "LABELS":
        if " AND " in value.upper():
            data["labels"] = [v.strip() for v in re.split(r"\s+AND\s+", value, flags=re.I)]
            data["label_operator"] = "and"
        elif " OR " in value.upper():
            data["labels"] = [v.strip() for v in re.split(r"\s+OR\s+", value, flags=re.I)]
            data["label_operator"] = "or"
        else:
            data["labels"] = _split_csv(value)
    elif key == "MEMBERS":
        data["members"] = _split_csv(value)
    elif key == "TITLE_PREFIX":
        data["title_prefix"] = value.strip("[]")
    elif key == "STATUS":
        or_match = STATUS_OR_PATTERN.search(value)
        if or_match:
            data["status"] = _split_status(or_match.group(1))
            data["status_operator"] = "or"
        elif " AND " in value.upper():
            data["status"] = _split_status(value)
            data["status_operator"] = "and"
        else:
            data["status"] = _split_status(value)
            data["status_operator"] = "or"
    elif key == "BOARD_ID":
        data["board_id"] = value.strip()
    elif key == "LISTS":
        data["lists"] = _split_csv(value)
    elif key == "PRIORITY":
        data["priority"] = [p.lower() for p in _split_csv(value)]
    elif key == "RISK_LEVELS":
        data["risk_levels"] = [r.lower() for r in _split_csv(value)]


def _normalize_payload(data: dict[str, Any]) -> dict[str, Any]:
    if "report_type" not in data and "type" in data:
        data["report_type"] = _map_report_type(str(data["type"]))
    if "metrics" not in data:
        data["metrics"] = ["LEAD_TIME", "CYCLE_TIME", "RISK_SCORE", "SLA"]
    if "limit" not in data:
        data["limit"] = 100
    if "sort_by" not in data:
        data["sort_by"] = "RISK_SCORE"
        data["sort_order"] = "DESC"
    return data


def _map_report_type(value: str) -> str:
    mapping = {
        "EXECUTIVE": "EXECUTIVO",
        "EXECUTIVO": "EXECUTIVO",
        "OPERATIONAL": "OPERACIONAL",
        "OPERACIONAL": "OPERACIONAL",
        "MEMBER": "MEMBRO",
        "MEMBRO": "MEMBRO",
        "TEAM": "EQUIPE",
        "EQUIPE": "EQUIPE",
        "LABEL": "ETIQUETA",
        "ETIQUETA": "ETIQUETA",
        "RISK": "RISCOS",
        "RISCOS": "RISCOS",
    }
    return mapping.get(value.strip().upper(), value.strip().upper())


def _map_period(value: str) -> str:
    mapping = {
        "LAST_30_DAYS": "last_30_days",
        "LAST_7_DAYS": "last_7_days",
        "LAST_15_DAYS": "last_15_days",
        "LAST_90_DAYS": "last_90_days",
        "TODAY": "today",
        "YESTERDAY": "yesterday",
        "THIS_MONTH": "this_month",
        "PREVIOUS_MONTH": "previous_month",
        "QUARTER": "quarter",
        "SEMESTER": "semester",
        "YEAR": "year",
    }
    return mapping.get(value.strip().upper(), value.strip().lower())


def _parse_sort(value: str) -> tuple[str, str]:
    parts = value.strip().split()
    if len(parts) >= 2:
        return parts[0].upper(), parts[1].upper()
    return value.strip().upper(), "DESC"


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[,;]", value) if item.strip()]


def _split_status(value: str) -> list[str]:
    items = re.split(r"\s+OR\s+|\s+AND\s+|,", value, flags=re.I)
    mapping = {
        "ATRASADO": "atrasado",
        "BLOQUEADO": "bloqueado",
        "ABERTO": "aberto",
        "EM ANDAMENTO": "em andamento",
        "CONCLUIDO": "concluido",
        "CONCLUÍDO": "concluido",
        "CANCELADO": "cancelado",
        "REABERTO": "reaberto",
        "OVERDUE": "atrasado",
        "BLOCKED": "bloqueado",
    }
    result = []
    for item in items:
        key = item.strip().upper()
        result.append(mapping.get(key, item.strip().lower()))
    return result
