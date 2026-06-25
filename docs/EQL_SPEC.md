# EOR Query Language (EQL) — Specification v1

**Version:** 1.0  
**Status:** Implemented  
**Engine:** Query Execution Engine (QEE)

---

## 1. Overview

EQL is the formal query language for all EOR reports. No report endpoint may apply ad-hoc filters — all logic flows through:

```
EQL string → Parser → AST → Validator → Query Planner → Execution Engine → Aggregation → Output
```

AI components may **only interpret** the structured output; they must **not** execute filters or compute metrics.

---

## 2. Query Structure

A valid EQL query contains one or more sections:

| Section | Required | Description |
|---------|----------|-------------|
| `REPORT` | Yes | Report type |
| `FILTER` | No | Filter predicates |
| `METRICS` | No | Metrics to compute (defaults apply) |
| `GROUP_BY` | No | Grouping dimensions |
| `SORT` | No | Sort order |
| `LIMIT` | Yes* | Max rows (*default 100 if omitted) |

Additionally, API calls must provide `board_id` in the JSON payload (or `BOARD_ID` in FILTER).

---

## 3. Syntax

### 3.1 REPORT section

```
REPORT:
TYPE = EXECUTIVE | OPERATIONAL | MEMBER | LABEL | PROJECT
```

Aliases: `EXECUTIVO` → `EXECUTIVE`, `OPERACIONAL` → `OPERATIONAL`, etc.

### 3.2 FILTER section

```
FILTER:
PERIOD = LAST_7_DAYS | LAST_15_DAYS | LAST_30_DAYS | LAST_90_DAYS | TODAY | YESTERDAY | THIS_MONTH | PREVIOUS_MONTH | QUARTER | SEMESTER | YEAR
PERIOD = CUSTOM_RANGE FROM 01/01/2026 TO 31/03/2026
TITLE_PREFIX = [AQUI]
TITLE_PREFIX = FINANCEIRO
LABELS = Financeiro AND Jurídico
LABELS = Financeiro OR Urgente
MEMBERS = Carlos OR João
STATUS = ATRASADO
STATUS = (ATRASADO OR BLOQUEADO)
RISK_SCORE >= 70
RISK_SCORE > 50
RISK_SCORE <= 30
```

### 3.3 METRICS section

```
METRICS:
LEAD_TIME, CYCLE_TIME, RISK_SCORE, SLA, THROUGHPUT, WIP
```

### 3.4 GROUP_BY section

```
GROUP_BY:
LABELS, MEMBERS, STATUS, PREFIX, LIST
```

### 3.5 SORT section

```
SORT:
RISK_SCORE DESC
LEAD_TIME ASC
```

### 3.6 LIMIT section

```
LIMIT:
100
```

---

## 4. Operators

| Operator | Usage |
|----------|-------|
| `=` | Equality |
| `>=`, `<=`, `>`, `<` | Comparison (numeric fields) |
| `AND` | Logical conjunction |
| `OR` | Logical disjunction |
| `( )` | Grouping |

---

## 5. AST Output (canonical)

```json
{
  "type": "EXECUTIVE",
  "board_id": "abc123",
  "filters": {
    "period": "LAST_30_DAYS",
    "title_prefix": "AQUI",
    "labels": {"values": ["Financeiro", "Jurídico"], "operator": "AND"},
    "members": {"values": ["Carlos"], "operator": "OR"},
    "status": {"values": ["ATRASADO"], "operator": "OR"},
    "risk_score": {"op": ">=", "value": 70}
  },
  "metrics": ["LEAD_TIME", "CYCLE_TIME", "RISK_SCORE", "SLA"],
  "group_by": ["LABELS", "MEMBERS"],
  "sort": [{"field": "RISK_SCORE", "order": "DESC"}],
  "limit": 100
}
```

---

## 6. Validation Rules

| Code | Condition |
|------|-----------|
| `SYNTAX_ERROR` | Unparseable input |
| `INVALID_FIELD` | Unknown filter/metric/group field |
| `INVALID_OPERATOR` | Unsupported operator for field |
| `MISSING_LIMIT` | Limit missing and no default (v1 default: 100) |
| `MISSING_REPORT_TYPE` | REPORT TYPE not specified |
| `MISSING_BOARD_ID` | board_id not in payload or FILTER |

---

## 7. Execution Strategy (QEE)

1. **Pushdown filters** on `timeline_events` for PERIOD
2. **Card snapshot** join for current state (labels, members, status)
3. **Enrichment** for priority/risk when needed
4. **Aggregation** for metrics and GROUP_BY
5. **Sort + LIMIT** last

---

## 8. Output Schema

```json
{
  "summary": {},
  "metrics": {},
  "grouped_data": {},
  "risks": {},
  "timeline": {},
  "recommendations": []
}
```

---

## 9. Example

```eql
REPORT:
TYPE = EXECUTIVE

FILTER:
PERIOD = LAST_30_DAYS
LABELS = Financeiro
MEMBERS = Carlos
STATUS = ATRASADO
TITLE_PREFIX = [AQUI]

METRICS:
LEAD_TIME, RISK_SCORE

LIMIT:
100
```

---

## 10. API

```
POST /api/reports/eql
POST /api/v1/reports/eql/

{
  "board_id": "YOUR_BOARD_ID",
  "query": "REPORT:\nTYPE = EXECUTIVE\n..."
}
```

---

## 11. Semantic Filters (BSL)

Business-level filters (resolved to technical filters + post-entity filtering):

```eql
FILTER:
PERIOD = LAST_30_DAYS
ENTITY_TYPE = INCIDENT
CATEGORY = FINANCEIRO
RISK_LEVEL >= HIGH
ENTITY_STATUS = ACTIVE
```

Semantic metrics: `INCIDENT_RATE`, `DELIVERY_SUCCESS_RATE`, `RISK_EXPOSURE_INDEX`, etc.

See `docs/BSL_ARCHITECTURE.md` for full semantic layer documentation.
