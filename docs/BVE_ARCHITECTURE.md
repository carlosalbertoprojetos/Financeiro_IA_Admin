# BVE — Business Value Engine

**Version:** 1.0

---

## Purpose

Translate the full EOR chain into measurable financial impact:

```
events → risks → decisions → actions → results → financial value
```

All values are computed from traceable inputs with confidence scores. Never invented.

---

## Pipeline Integration

```
DAL (execute action)
  → OLE (effectiveness)
  → BVE (financial value)
```

After each executed action, `record_action_value()` persists:
- avoided_loss (from risk before/after)
- productivity benefit (hours saved × hourly rate)
- ROI (benefit vs action cost)
- full audit_json for traceability

---

## Module Layout

```
apps/intelligence/services/business_value/
├── config.py                 # BVE_HOURLY_RATE_BRL, BVE_BASE_IMPACT_BRL
├── models/business_value.py  # BusinessValueRecord dataclass
├── cost_engine/calculator.py # delay, rework, blocking, waiting, SLA
├── productivity/engine.py    # hours saved, capacity freed
├── risk_value/engine.py      # expected_loss, avoided_loss
├── roi/engine.py             # action ROI
├── attribution/engine.py     # by area/team/project/member
├── trends/engine.py          # monthly/quarterly/annual
└── pipeline.py               # record_action_value + dashboard
```

---

## Value Model

Table: `business_value_records`

| Field | Description |
|-------|-------------|
| source_id | decision_id or event id |
| source_type | action_execution, delay_event, etc. |
| value_type | ACTION_ROI, DELAY_COST, etc. |
| estimated_cost | Action + operational costs |
| estimated_benefit | Projected benefit |
| realized_benefit | Measured post-action benefit |
| avoided_loss | expected_loss(before) - expected_loss(after) |
| confidence_score | 0-1 based on data quality |
| roi_pct | ((benefit - cost) / cost) × 100 |
| audit_json | Full calculation breakdown |

---

## Cost Engine

| Type | Formula |
|------|---------|
| Delay | days_overdue × hours/day × hourly_rate × assignees |
| Rework | rework_events × hours × hourly_rate |
| Blocking | blocked_hours × members × hourly_rate |
| Waiting | wait_hours × hourly_rate |
| SLA breach | (probability/100) × impact_brl |

---

## Risk Value Engine

```
probability = risk_score / 100
expected_loss = probability × impact_brl
avoided_loss = expected_loss(before) - expected_loss(after)
```

Example: risk_score=90, impact=R$20.000 → expected_loss=R$18.000

---

## Action ROI

```
roi_pct = (avoided_loss + realized_benefit - action_cost) / action_cost × 100
```

Action costs configurable via `BVE_ACTION_COST_{ACTION_TYPE}` env vars.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/value/dashboard/` | Executive value dashboard |
| GET | `/api/value/projects/` | ROI by project |
| GET | `/api/value/teams/` | ROI by team |
| GET | `/api/value/actions/` | ROI by action type |
| GET | `/api/value/trends/` | Monthly/quarterly/annual trends |

Also under `/api/v1/value/`.

Query params: `board_id`, `days`

---

## Configuration

```env
BVE_HOURLY_RATE_BRL=150
BVE_BASE_IMPACT_BRL=20000
BVE_HOURS_PER_WORKDAY=8
BVE_ACTION_COST_ESCALATE_TASK=200
```

---

## Critical Rules

- **Estimated** vs **realized** vs **avoided** always separated
- Every record includes `confidence_score` and `audit_json`
- Narratives only generated when sufficient records exist

---

## Tests

```bash
python manage.py test apps.intelligence.tests.business_value
```
