from __future__ import annotations

from enum import Enum


class ReportMetric(str, Enum):
    LEAD_TIME = "LEAD_TIME"
    CYCLE_TIME = "CYCLE_TIME"
    RISK_SCORE = "RISK_SCORE"
    SLA = "SLA"
    THROUGHPUT = "THROUGHPUT"
    WIP = "WIP"


class GroupByField(str, Enum):
    LABELS = "LABELS"
    MEMBERS = "MEMBERS"
    STATUS = "STATUS"
    PREFIX = "PREFIX"
    LIST = "LIST"


class SortField(str, Enum):
    RISK_SCORE = "RISK_SCORE"
    LEAD_TIME = "LEAD_TIME"
    CYCLE_TIME = "CYCLE_TIME"
    TITLE = "TITLE"
    DUE_DATE = "DUE_DATE"
    UPDATED_AT = "UPDATED_AT"


class SortOrder(str, Enum):
    ASC = "ASC"
    DESC = "DESC"


class StatusOperator(str, Enum):
    OR = "or"
    AND = "and"
