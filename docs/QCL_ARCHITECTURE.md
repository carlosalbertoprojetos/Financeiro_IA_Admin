# EOR Query Compilation Layer (QCL) — Architecture

**Version:** 1.0  
**Status:** Implemented

---

## Pipeline

```
EQL string
    ↓
Parser (eql/parser.py)
    ↓
AST Validator (eql/validator.py)
    ↓
Compiler (query_engine/compiler/)          ← NEW
    ↓
Optimizer (query_engine/optimizer/)        ← NEW
    ↓
Cost Estimator (query_engine/cost_estimator/)  ← NEW
    ↓
Guard (query_engine/guard/)                ← NEW
    ↓
Execution Engine (query_engine/executor.py)    ← REFACTORED
    ↓
Aggregation Layer (query_engine/aggregation.py)
    ↓
Report Output
```

---

## Separation of Responsibilities

| Module | Can Do | Cannot Do |
|--------|--------|-----------|
| **Compiler** | AST → Query Plan | Execute data, optimize |
| **Optimizer** | Rewrite plan | Execute data |
| **Cost Estimator** | Estimate cost | Execute data |
| **Guard** | Reject dangerous queries | Execute or optimize |
| **Executor** | Execute optimized plan | Optimize, parse EQL |

---

## Query Plan Structure

```json
{
  "scan": {"source": "timeline_events", "secondary_sources": ["cards"]},
  "filters": [{"field": "period", "stage": "scan", "pushdown": true}],
  "pre_aggregations": [{"dimension": "LABELS", "strategy": "hash"}],
  "grouping": ["LABELS"],
  "sorting": [{"field": "RISK_SCORE", "order": "DESC"}],
  "limit": 100,
  "execution_strategy": "PARALLEL"
}
```

---

## Optimization Rules

1. **Filter Pushdown** — filters applied at earliest stage (scan > post_scan > post_join)
2. **Source Selection** — `timeline_events` for period, `enriched_context` for labels/prefix
3. **Early Limit** — limit applied before heavy aggregations when ≤ 500
4. **Grouping Strategy** — pre-aggregate by dimension before metrics
5. **Parallel Execution** — enabled when labels/members/status filters are independent

---

## Guard Rules

| Rule | Error Code |
|------|------------|
| Cost > 85 | `QUERY_COST_REJECTED` |
| Missing LIMIT | `MISSING_LIMIT` |
| Filters without PERIOD | `MISSING_TEMPORAL_SCOPE` |
| GROUP BY without LIMIT ≤ 500 | `GROUP_BY_WITHOUT_LIMIT` |

---

## Observability

Table: `report_query_execution_trace`

Fields: `query_raw`, `ast`, `query_plan`, `optimized_plan`, `estimated_cost`, `actual_cost`, `execution_time_ms`, `cache_hit`, `rejected_by_guard`

---

## API

Unchanged: `POST /api/reports/eql/`

Response now includes:
- `query_plan`
- `optimized_plan`
- `cost_estimate`
- `actual_cost`
- `execution_plan`
