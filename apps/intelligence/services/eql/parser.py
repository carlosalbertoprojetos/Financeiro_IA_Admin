from __future__ import annotations

import re
from typing import Any

from apps.intelligence.services.eql.ast import EQLQuery, ListFilter, SortSpec
from apps.intelligence.services.eql.errors import SyntaxError as EQLSyntaxError

SECTION_HEADERS = frozenset({"REPORT", "FILTER", "METRICS", "GROUP_BY", "SORT", "LIMIT"})
REPORT_TYPES = {
    "EXECUTIVE": "EXECUTIVE",
    "EXECUTIVO": "EXECUTIVE",
    "OPERATIONAL": "OPERATIONAL",
    "OPERACIONAL": "OPERATIONAL",
    "MEMBER": "MEMBER",
    "MEMBRO": "MEMBER",
    "LABEL": "LABEL",
    "ETIQUETA": "LABEL",
    "PROJECT": "PROJECT",
    "PROJETO": "PROJECT",
}
PERIOD_MAP = {
    "LAST_7_DAYS": "LAST_7_DAYS",
    "LAST_15_DAYS": "LAST_15_DAYS",
    "LAST_30_DAYS": "LAST_30_DAYS",
    "LAST_90_DAYS": "LAST_90_DAYS",
    "TODAY": "TODAY",
    "YESTERDAY": "YESTERDAY",
    "THIS_MONTH": "THIS_MONTH",
    "PREVIOUS_MONTH": "PREVIOUS_MONTH",
    "QUARTER": "QUARTER",
    "SEMESTER": "SEMESTER",
    "YEAR": "YEAR",
}
STATUS_MAP = {
    "ATRASADO": "atrasado",
    "OVERDUE": "atrasado",
    "BLOQUEADO": "bloqueado",
    "BLOCKED": "bloqueado",
    "ABERTO": "aberto",
    "OPEN": "aberto",
    "EM ANDAMENTO": "em andamento",
    "IN_PROGRESS": "em andamento",
    "CONCLUIDO": "concluido",
    "CONCLUÍDO": "concluido",
    "COMPLETED": "concluido",
    "CANCELADO": "cancelado",
    "REABERTO": "reaberto",
}


def parse_eql(text: str, *, board_id: str = "") -> EQLQuery:
    """Parse EQL text into a structured EQLQuery AST."""
    sections = _split_sections(text)
    query = EQLQuery(board_id=board_id)

    for section_name, lines in sections.items():
        if section_name == "REPORT":
            _parse_report_section(query, lines)
        elif section_name == "FILTER":
            _parse_filter_section(query, lines)
        elif section_name == "METRICS":
            query.metrics = _parse_csv_list(_join_lines(lines))
        elif section_name == "GROUP_BY":
            query.group_by = [g.strip().upper() for g in _parse_csv_list(_join_lines(lines))]
        elif section_name == "SORT":
            query.sort = _parse_sort(lines)
        elif section_name == "LIMIT":
            query.limit = _parse_limit(lines)

    if not query.type:
        raise EQLSyntaxError("REPORT TYPE is required", code="MISSING_REPORT_TYPE")

    return query


def _split_sections(text: str) -> dict[str, list[tuple[int, str]]]:
    sections: dict[str, list[tuple[int, str]]] = {}
    current = "_PREAMBLE"
    sections[current] = []

    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        header_match = re.match(r"^(REPORT|FILTER|METRICS|GROUP_BY|SORT|LIMIT)\s*:\s*(.*)$", line, re.I)
        if header_match:
            current = header_match.group(1).upper()
            sections.setdefault(current, [])
            remainder = header_match.group(2).strip()
            if remainder:
                sections[current].append((line_no, remainder))
            continue
        sections.setdefault(current, [])
        sections[current].append((line_no, line))

    return {k: v for k, v in sections.items() if k in SECTION_HEADERS or k == "_PREAMBLE"}


def _parse_report_section(query: EQLQuery, lines: list[tuple[int, str]]) -> None:
    for line_no, line in lines:
        match = re.match(r"TYPE\s*=\s*(.+)$", line, re.I)
        if match:
            raw = match.group(1).strip().upper()
            query.type = REPORT_TYPES.get(raw, raw)
            return
        raise EQLSyntaxError(f"Invalid REPORT line: {line}", line=line_no)


def _parse_filter_section(query: EQLQuery, lines: list[tuple[int, str]]) -> None:
    filters = query.filters
    for line_no, line in lines:
        if re.match(r"PERIOD\s*=", line, re.I):
            filters["period"] = _parse_period(line)
            continue
        if re.match(r"TITLE_PREFIX\s*=", line, re.I):
            val = re.split(r"=", line, 1)[1].strip().strip("[]")
            filters["title_prefix"] = val
            continue
        if re.match(r"LABELS\s*=", line, re.I):
            val = re.split(r"=", line, 1)[1].strip()
            filters["labels"] = _parse_list_filter(val)
            continue
        if re.match(r"MEMBERS\s*=", line, re.I):
            val = re.split(r"=", line, 1)[1].strip()
            filters["members"] = _parse_list_filter(val, default_op="OR")
            continue
        if re.match(r"STATUS\s*=", line, re.I):
            val = re.split(r"=", line, 1)[1].strip()
            filters["status"] = _parse_status_filter(val)
            continue
        if re.match(r"BOARD_ID\s*=", line, re.I):
            query.board_id = re.split(r"=", line, 1)[1].strip()
            continue
        if re.match(r"ENTITY_TYPE\s*=", line, re.I):
            val = re.split(r"=", line, 1)[1].strip()
            filters["entity_type"] = _parse_list_filter(val, default_op="OR")
            continue
        if re.match(r"CATEGORY\s*=", line, re.I):
            val = re.split(r"=", line, 1)[1].strip().strip("[]")
            filters["category"] = val.upper()
            continue
        if re.match(r"ENTITY_STATUS\s*=", line, re.I):
            val = re.split(r"=", line, 1)[1].strip()
            inner = re.match(r"\((.+)\)", val.strip())
            expr = inner.group(1) if inner else val
            if re.search(r"\s+OR\s+", expr, re.I):
                parts = re.split(r"\s+OR\s+", expr, flags=re.I)
            else:
                parts = re.split(r"[,;]", expr)
            filters["entity_status"] = {
                "values": [p.strip().upper() for p in parts if p.strip()],
                "operator": "OR",
            }
            continue
        risk_level = re.match(r"RISK_LEVEL\s*(>=|<=|>|<|=)\s*(\w+)", line, re.I)
        if risk_level:
            filters["risk_level"] = {"op": risk_level.group(1), "value": risk_level.group(2).upper()}
            continue
        comp = re.match(r"(RISK_SCORE|LEAD_TIME|CYCLE_TIME)\s*(>=|<=|>|<|=)\s*([\d.]+)", line, re.I)
        if comp:
            field = comp.group(1).upper()
            filters[field.lower()] = {"op": comp.group(2), "value": float(comp.group(3))}
            continue
        raise EQLSyntaxError(f"Invalid FILTER line: {line}", line=line_no)


def _parse_period(line: str) -> dict[str, Any]:
    val = re.split(r"=", line, 1)[1].strip().upper()
    custom = re.match(r"CUSTOM_RANGE\s+FROM\s+(\S+)\s+TO\s+(\S+)", val, re.I)
    if custom:
        return {"preset": "CUSTOM", "from": custom.group(1), "to": custom.group(2)}
    preset = PERIOD_MAP.get(val, val)
    return {"preset": preset}


def _parse_list_filter(value: str, *, default_op: str = "AND") -> dict[str, Any]:
    if re.search(r"\s+AND\s+", value, re.I):
        parts = re.split(r"\s+AND\s+", value, flags=re.I)
        return {"values": [p.strip() for p in parts if p.strip()], "operator": "AND"}
    if re.search(r"\s+OR\s+", value, re.I):
        parts = re.split(r"\s+OR\s+", value, flags=re.I)
        return {"values": [p.strip() for p in parts if p.strip()], "operator": "OR"}
    return {"values": _parse_csv_list(value), "operator": default_op}


def _parse_status_filter(value: str) -> dict[str, Any]:
    inner = re.match(r"\((.+)\)", value.strip())
    expr = inner.group(1) if inner else value
    if re.search(r"\s+OR\s+", expr, re.I):
        parts = re.split(r"\s+OR\s+", expr, flags=re.I)
        op = "OR"
    elif re.search(r"\s+AND\s+", expr, re.I):
        parts = re.split(r"\s+AND\s+", expr, flags=re.I)
        op = "AND"
    else:
        parts = [expr]
        op = "OR"
    values = [STATUS_MAP.get(p.strip().upper(), p.strip().lower()) for p in parts if p.strip()]
    return {"values": values, "operator": op}


def _parse_sort(lines: list[tuple[int, str]]) -> list[SortSpec]:
    specs: list[SortSpec] = []
    for _, line in lines:
        parts = line.strip().split()
        if len(parts) >= 2:
            specs.append(SortSpec(parts[0].upper(), parts[1].upper()))
        elif len(parts) == 1:
            specs.append(SortSpec(parts[0].upper(), "DESC"))
    return specs or [SortSpec("RISK_SCORE", "DESC")]


def _parse_limit(lines: list[tuple[int, str]]) -> int:
    for _, line in lines:
        digits = re.sub(r"\D", "", line)
        if digits:
            return int(digits)
    return 100


def _parse_csv_list(text: str) -> list[str]:
    return [item.strip().upper() for item in re.split(r"[,;]", text) if item.strip()]


def _join_lines(lines: list[tuple[int, str]]) -> str:
    return ", ".join(line for _, line in lines)
