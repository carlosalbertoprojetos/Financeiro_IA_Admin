# ODTL — Observability + Decision Trace Layer

**Version:** 1.0

---

## Purpose

Full decision traceability from EQL query to final insight. Answers:

- Where did this insight come from?
- Which rules influenced the output?
- Which events contributed to each metric?
- What path did the query take?

---

## Pipeline

```
EQL → Query Engine → Semantic Layer → CMGL → ODTL (trace) → Output
```

Every execution produces:
- `trace_id` — unique per execution
- `query_id` — deterministic hash (reproducibility)

---

## DecisionTrace Structure

```json
{
  "trace_id": "uuid",
  "query_id": "sha256...",
  "steps": [],
  "inputs": [],
  "transformations": [],
  "semantic_mappings": [],
  "metrics_calculated": [],
  "rules_applied": [],
  "ai_decisions": [],
  "query_lineage": {},
  "execution_path": [],
  "errors": []
}
```

---

## Modules

| Module | Path |
|--------|------|
| Trace Model | `observability/trace/` |
| Query Lineage | `observability/lineage/query_lineage.py` |
| Metrics Lineage | `observability/lineage/metrics_lineage.py` |
| Semantic Trace | `observability/semantic_trace.py` |
| Execution Trace | `observability/execution_trace.py` |
| AI Trace | `observability/ai_trace.py` |
| Error Trace | `observability/error_trace.py` |
| Storage | `decision_traces` table |
| Dashboard | `observability/dashboard.py` |

---

## API

```
GET /api/traces/
GET /api/traces/{trace_id}/
GET /api/traces/query/{query_id}/
GET /api/traces/insights/
GET /api/traces/dashboard/
```

Also available under `/api/v1/traces/`.

---

## Debug Mode

Set environment variable:

```
EOR_DEBUG_MODE=true
```

When enabled, API responses include:
- `decision_trace` — full trace object
- `metrics_lineage` — per-metric lineage

---

## Storage

Table: `decision_traces`

Fields: `trace_id`, `query_id`, `query`, `execution_time_ms`, `status`, `summary`, `full_trace_json`
