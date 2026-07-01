# POCL Architecture — Pilot Operational Control Loop

**Version:** 1.0  
**Mode:** Human-in-the-loop operational pilot

---

## Objective

Activate EOR as a **daily decision support system** on a real board, measuring continuous impact on operational decisions — not architecture or test coverage.

---

## Pilot Scope

| Parameter | Default |
|-----------|---------|
| Board | `POCL_BOARD_ID` env or `PilotConfig` record |
| Team | `POCL_TEAM_NAME` |
| Duration | 5 to 10 days |
| Auto-execution | **DISABLED** (`DAL_AUTO_EXECUTION=false`) |

---

## Control Loop

```
Trello event/sync
  → Timeline
  → EQL + Semantic Layer
  → DAL decision proposals (persist=True)
  → Human approval queue
  → Action execution (on approve)
  → OLE learning + BVE value
  → Impact follow-ups (24h / 72h / 7d)
  → Executive daily report
```

---

## Components

| # | Component | Path |
|---|-----------|------|
| 1 | Pilot Control System | `services/pilot/config.py` |
| 2 | Decision Stream Engine | `services/pilot/decision_stream.py` |
| 3 | Daily Cycle Engine | `services/pilot/daily_cycle.py` |
| 4 | Feedback Capture | `services/pilot/feedback.py` + `DecisionFeedbackRecord` |
| 5 | Real Impact Tracker | `services/pilot/impact_tracker.py` + `ActionImpactFollowUp` |
| 6 | Executive Daily Report | `services/pilot/report_generator.py` → `reports/executive_daily_report.md` |
| 7 | Pilot Evaluation | `services/pilot/evaluation.py` → `docs/PILOT_EVALUATION_REPORT.md` |

---

## Models

| Model | Table | Purpose |
|-------|-------|---------|
| `PilotConfig` | `pilot_configs` | Active pilot scope |
| `PilotCycleRun` | `pilot_cycle_runs` | Cycle audit log |
| `DecisionFeedbackRecord` | `decision_feedback` | Accept / ignore / modify |
| `ActionImpactFollowUp` | `action_impact_followups` | Delayed real impact |

---

## Daily Cycle

| Phase | Time (Celery Beat) | Actions |
|-------|-------------------|---------|
| **Morning** | 08:00 | Sync + backlog/risk analysis + decision stream |
| **Intraday** | 09:00–18:00 hourly | Sync + change detection + interventions |
| **EOD** | 19:00 | Impact follow-ups + executive report |

Enable scheduler: `POCL_ENABLED=true` + Celery Beat worker.

The pilot can only be activated for a board that already exists in the local
Trello projection and is not closed. Run a real Trello sync first; POCL does not
create synthetic boards or simulated metrics.

---

## API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/pilot/` | Status + metrics |
| POST | `/api/pilot/activate/` | Start pilot |
| POST | `/api/pilot/stream/` | Run decision stream |
| POST | `/api/pilot/cycle/` | Run daily phase |
| POST | `/api/pilot/feedback/` | Record human feedback |
| POST | `/api/pilot/followups/` | Process due impact measurements |
| POST | `/api/pilot/report/` | Generate daily report |
| GET | `/api/pilot/evaluate/` | Pilot success metrics |

Also available under `/api/v1/pilot/`.

---

## CLI

```bash
python manage.py pocl activate --board-id BOARD_ID --team "Ops Team"
python manage.py pocl stream --board-id BOARD_ID
python manage.py pocl cycle --board-id BOARD_ID --phase morning
python manage.py pocl followups --board-id BOARD_ID
python manage.py pocl report --board-id BOARD_ID
python manage.py pocl evaluate --board-id BOARD_ID
```

---

## Human-in-the-Loop Rules

1. `DAL_AUTO_EXECUTION` must be `false`
2. All `SEMI_AUTOMATIC` actions require approval via `/api/actions/approve/`
3. Rejections recorded as `IGNORED` feedback
4. Approvals recorded as `ACCEPTED` feedback
5. Modified actions recorded as `MODIFIED` via `/api/pilot/feedback/`
6. Pilot duration must be 5-10 days
7. Missing card state marks impact follow-up as `SKIPPED`; it is never inferred

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Acceptance rate | ≥60% |
| Pilot success score | ≥70/100 |
| Impact follow-ups measured | Real card state at T+24h/72h/7d |
| BVE prediction error | Tracked in `estimated_vs_realized_json` |
| Inferred impact | Not allowed |

---

## Environment

```env
POCL_ENABLED=true
POCL_ACTIVE=true
POCL_BOARD_ID=66c6308377ff5ddcb67c7fb9
POCL_TEAM_NAME=Operations
DAL_AUTO_EXECUTION=false
```

---

## Integration Points

- **Post-sync hook:** `integrations/trello/services/sync.py` → decision stream when pilot active
- **Post-execution:** `decision_layer/orchestrator.py` → schedule follow-ups + capture acceptance
- **Reject flow:** `views_actions.py` → feedback + `mark_rejected`
