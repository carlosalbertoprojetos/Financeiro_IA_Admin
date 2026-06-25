# BVE ROI Model

**Version:** 1.0

---

## Principles

1. All values derived from **measurable inputs** (risk scores, hours, configured rates).
2. Three buckets always separated: **estimated**, **realized**, **avoided**.
3. Every record includes `confidence_score` and `audit_json`.

---

## Expected Loss

```
probability = risk_score / 100
impact_brl = BVE_BASE_IMPACT_BRL × (risk_score / 100)   [or explicit impact]
expected_loss = probability × impact_brl
```

Example: risk_score=90, base_impact=R$20.000 → expected_loss=R$18.000

---

## Avoided Loss (post-action)

```
avoided_loss = max(0, expected_loss_before - expected_loss_after)
```

---

## Action ROI

```
total_benefit = avoided_loss + realized_benefit
net_value = total_benefit - action_cost
roi_pct = (net_value / action_cost) × 100
```

Example:
- ESCALATE_TASK cost: R$200
- Avoided loss: R$5.000
- ROI: 2.400%

---

## Cost Components

| Type | Formula |
|------|---------|
| Delay | days_overdue × hours/day × hourly_rate × assignees |
| Rework | rework_events × hours × hourly_rate |
| Blocking | blocked_hours × members × hourly_rate |
| Waiting | wait_hours × hourly_rate |
| SLA breach | (probability/100) × impact_brl |

---

## Productivity Value

```
hours_saved = (risk_before - risk_after) × hours_per_risk_point
estimated_benefit = hours_saved × BVE_HOURLY_RATE_BRL
```

---

## Confidence Scoring

Weighted average of:
- Risk measurement confidence (0.8 when risk_score > 0)
- Productivity confidence (0.75 when risk delta measured)
- ROI confidence (0.85 when avoided_loss > 0)
- Cost input confidence (varies by cost type)

---

## Configuration

```env
BVE_HOURLY_RATE_BRL=150
BVE_BASE_IMPACT_BRL=20000
BVE_HOURS_PER_WORKDAY=8
BVE_ACTION_COST_ESCALATE_TASK=200
```

---

## Audit Trail

Every `BusinessValueRecordModel` stores full calculation breakdown in `audit_json`:

```json
{
  "avoided_loss_detail": { ... },
  "productivity": { ... },
  "roi": { ... },
  "operational_costs": [ ... ],
  "before": { "risk_score": 85 },
  "after": { "risk_score": 40 }
}
```

---

## Narrative Generation

Dashboard narratives only generated when `count > 0` records exist:

> "Action ESCALATE_TASK avoided estimated losses of R$ 48,000.00 in the last 90 days, with average ROI of 1,240.0%"

All figures traceable to `business_value_records` table.
