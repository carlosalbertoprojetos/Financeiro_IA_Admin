# OLE — Organizational Learning Engine

**Version:** 1.0

---

## Purpose

Transform executed decisions and actions into reusable organizational knowledge. Every effectiveness score is computed from real before/after measurements — no AI-invented results.

Answers:
- Which actions work best?
- Which actions reduce risk most?
- Which interventions fail?
- Which patterns produce the best outcomes?

---

## Architecture

```
Executed Action (DAL)
        │
        ▼
Outcome Engine ──► SUCCESS | LOW_IMPACT | FAILURE | NEUTRAL
        │
        ▼
Effectiveness Scoring (0-100)
        │
        ├─► DecisionEffectivenessRecord (DB)
        ├─► Organizational Memory (lessons + playbook candidates)
        ├─► Pattern Analyzer
        ├─► Playbook Engine
        ├─► Knowledge Graph
        └─► Action Generator (recommendation evolution)
```

---

## Module Layout

```
apps/intelligence/services/organizational_learning/
├── models/effectiveness.py       # DecisionEffectiveness dataclass
├── outcomes/evaluator.py         # Action outcome classification
├── scoring/effectiveness_scorer.py
├── patterns/analyzer.py          # Effective/ineffective action detection
├── playbooks/engine.py           # Evidence-based playbooks
├── knowledge_graph/graph.py      # Problem → Action → Result → Effectiveness
├── memory/storage.py             # organizational_memory table
├── maturity/index.py             # EOR Maturity Index
└── pipeline.py                   # record_action_learning + dashboard
```

---

## Decision Effectiveness Model

Table: `decision_effectiveness`

| Field | Description |
|-------|-------------|
| decision_id | Source decision |
| action_type | ESCALATE_TASK, etc. |
| risk_before / risk_after | From risk engine (real card data) |
| sla_before / sla_after | SLA breach probability proxy from risk engine |
| execution_time | Milliseconds |
| outcome_score | 0-100 |
| effectiveness_score | 0-100 weighted score |
| outcome_label | SUCCESS, LOW_IMPACT, FAILURE, NEUTRAL |

---

## Outcome Classification

| Outcome | Criteria (real measurements) |
|---------|------------------------------|
| SUCCESS | Risk reduced ≥15pts or ≥15%, problem resolved |
| LOW_IMPACT | Delta < 5 points |
| FAILURE | Risk or SLA increased |
| NEUTRAL | CREATE_ALERT (informational) |

---

## Effectiveness Scoring

Components:
- Risk reduction (up to 40 pts)
- SLA improvement (up to 30 pts)
- Problem resolution bonus (20 pts)
- Bottleneck resolution bonus (10 pts)
- Time penalty for slow resolution

---

## Playbooks

Generated only when `sample_size >= min_sample_size` (default 3).

Example:
```json
{
  "when": {"category": "FINANCEIRO", "condition": "FINANCEIRO + risco alto"},
  "recommended_action": "ESCALATE_TASK",
  "historical_effectiveness_pct": 89.0,
  "sample_size": 12,
  "evidence_based": true
}
```

---

## Knowledge Graph

Nodes: `problem`, `action`, `result`, `effectiveness`, `lesson`

Edges: `triggered`, `produced`, `measured_as`, `recommends`

---

## Recommendation Evolution

`action_generator.py` now:
1. Attaches `historical_success_rate_pct` to action params when data exists
2. Ranks actions by historical effectiveness
3. Injects playbook recommendations when matched

---

## EOR Maturity Index

Scale 0-100, weighted components:

| Component | Weight |
|-----------|--------|
| SLA | 20% |
| Effectiveness | 30% |
| Risk | 20% |
| Productivity | 15% |
| Learning | 15% |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/learning/dashboard/` | Executive learning dashboard |
| GET | `/api/learning/patterns/` | Action pattern analysis |
| GET | `/api/learning/playbooks/` | Evidence-based playbooks |
| GET | `/api/learning/knowledge-graph/` | Knowledge graph |
| GET | `/api/learning/memory/` | Organizational memory |
| GET | `/api/learning/maturity/` | EOR Maturity Index |
| GET | `/api/learning/actions/{type}/` | Historical stats per action |

Also under `/api/v1/learning/`.

---

## Integration

After every executed action in DAL orchestrator:
```python
record_action_learning(decision_id, action_type, before, after, impact, ...)
```

---

## Evidence-Based Narrative

Dashboard generates statements like:
> "Action ESCALATE_TASK has 89% success rate across 12 executions, with average risk reduction of 47%."

Only when sufficient historical records exist.

---

## Tests

```bash
python manage.py test apps.intelligence.tests.organizational_learning
```
