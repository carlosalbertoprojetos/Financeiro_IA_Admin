from __future__ import annotations

from apps.intelligence.services.eql.ast import EQLQuery
from apps.intelligence.services.eql.errors import (
    InvalidFieldError,
    InvalidOperatorError,
    MissingBoardIdError,
    MissingLimitError,
    MissingReportTypeError,
)

VALID_REPORT_TYPES = frozenset({"EXECUTIVE", "OPERATIONAL", "MEMBER", "LABEL", "PROJECT"})
VALID_METRICS = frozenset({"LEAD_TIME", "CYCLE_TIME", "RISK_SCORE", "SLA", "THROUGHPUT", "WIP"})
VALID_GROUP_BY = frozenset({"LABELS", "MEMBERS", "STATUS", "PREFIX", "LIST"})
VALID_SORT_FIELDS = frozenset({"RISK_SCORE", "LEAD_TIME", "CYCLE_TIME", "TITLE", "DUE_DATE", "UPDATED_AT"})
VALID_FILTER_FIELDS = frozenset({
    "period", "title_prefix", "labels", "members", "status",
    "risk_score", "lead_time", "cycle_time", "board_id",
    "entity_type", "category", "risk_level", "entity_status",
})
VALID_SEMANTIC_METRICS = frozenset({
    "INCIDENT_RATE", "DELIVERY_SUCCESS_RATE", "RISK_EXPOSURE_INDEX",
    "TEAM_LOAD_BALANCE", "OPERATIONAL_EFFICIENCY", "BOTTLENECK_DENSITY",
    "SLA_BREACH_PROBABILITY",
})
VALID_COMP_OPS = frozenset({"=", ">=", "<=", ">", "<"})
MAX_LIMIT = 1000
DEFAULT_LIMIT = 100


def validate_eql(query: EQLQuery, *, require_board_id: bool = True) -> EQLQuery:
    """Validate EQL AST; raise EQLError subclasses on failure."""
    if not query.type:
        raise MissingReportTypeError("REPORT TYPE is required")
    if query.type not in VALID_REPORT_TYPES:
        raise InvalidFieldError(f"Invalid report type: {query.type}")

    if require_board_id and not query.board_id:
        raise MissingBoardIdError("board_id is required in API payload or FILTER section")

    if query.limit is None or query.limit <= 0:
        raise MissingLimitError("LIMIT must be a positive integer")
    if query.limit > MAX_LIMIT:
        raise InvalidFieldError(f"LIMIT exceeds maximum ({MAX_LIMIT})")

    for metric in query.metrics:
        m = metric.upper()
        if m not in VALID_METRICS and m not in VALID_SEMANTIC_METRICS:
            raise InvalidFieldError(f"Invalid metric: {metric}")

    for group in query.group_by:
        if group.upper() not in VALID_GROUP_BY:
            raise InvalidFieldError(f"Invalid GROUP_BY field: {group}")

    for sort_spec in query.sort:
        if sort_spec.field not in VALID_SORT_FIELDS:
            raise InvalidFieldError(f"Invalid SORT field: {sort_spec.field}")
        if sort_spec.order not in ("ASC", "DESC"):
            raise InvalidOperatorError(f"Invalid sort order: {sort_spec.order}")

    for key in query.filters:
        if key not in VALID_FILTER_FIELDS:
            raise InvalidFieldError(f"Invalid filter field: {key}")
        val = query.filters[key]
        if isinstance(val, dict) and "op" in val:
            if val["op"] not in VALID_COMP_OPS:
                raise InvalidOperatorError(f"Invalid operator: {val['op']}")

    if not query.limit:
        query.limit = DEFAULT_LIMIT

    return query
