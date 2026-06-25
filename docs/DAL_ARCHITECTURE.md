# DAL — Decision Action Layer

**Version:** 1.0

---

## Purpose

Transform EOR from analysis-only to action-capable. Closes the loop:

```
data → insight → decision → action → feedback
```

Insights are **not** auto-executed by default. Every action is traceable, auditable, and guarded.

---

## Architecture

```
Query / Intelligence Pipeline
         │
         ▼
   Semantic Layer (entities, insights)
         │
         ▼
┌─────────────────────┐
│ Action Generator    │  risks → structured actions
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Prioritizer         │  ordered action queue
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Safety Guards       │  approval, rate limits, loop detection
└─────────┬───────────┘
          │
     ┌────┴────┐
     │         │
  MANUAL   SEMI_AUTO / AUTO
     │         │
     ▼         ▼
 Suggest   Approval Flow
               │
               ▼
        Execution Orchestrator
               │
     ┌─────────┼─────────┐
     ▼         ▼         ▼
  Trello   Internal   Webhook
               │
               ▼
        Feedback Loop → risk model
               │
               ▼
        ODTL (actions_taken)
```

---

## Module Layout

```
apps/intelligence/services/decision_layer/
├── models/decision_object.py   # DecisionObject, RecommendedAction
├── action_generator.py         # insight → actions
├── prioritizer.py              # scoring + queue ordering
├── orchestrator.py             # execution coordinator
├── trello_executor.py          # Trello API writes
├── pipeline.py                 # EOR core integration hook
├── approval/flow.py              # human approval
├── feedback/loop.py              # post-action impact
├── guards/rules.py               # safety guardrails
└── queue/manager.py              # persistent queue + retry/DLQ
```

---

## Decision Object

```json
{
  "id": "uuid",
  "source_trace_id": "odtl-trace-id",
  "insight": "Risk detected on [AQUI] Revisar Contrato",
  "priority": "HIGH",
  "recommended_actions": [
    {
      "action_type": "ESCALATE_TASK",
      "execution_mode": "SEMI_AUTOMATIC",
      "target_card_id": "card_aqui",
      "params": {"reason": "critical_risk"}
    }
  ],
  "status": "OPEN",
  "owner": "system",
  "context": {},
  "execution_history": []
}
```

---

## Action Types

| Type | Mode | Description |
|------|------|-------------|
| `REASSIGN_OWNER` | MANUAL | Review/suggest ownership change |
| `ESCALATE_TASK` | SEMI_AUTOMATIC | Comment + priority bump on Trello |
| `REOPEN_CARD` | SEMI_AUTOMATIC | Reopen closed card |
| `CREATE_ALERT` | AUTOMATIC* | Internal alert (requires DAL_AUTO_EXECUTION) |
| `ADJUST_PRIORITY` | SEMI_AUTOMATIC | Move card to top of list |
| `MANAGERIAL_INTERVENTION` | MANUAL | Suggestion only |
| `ADD_COMMENT` | AUTOMATIC* | Add Trello comment |
| `MOVE_CARD` | SEMI_AUTOMATIC | Move to another list |
| `WEBHOOK_NOTIFY` | AUTOMATIC* | External webhook |

\* Automatic execution disabled unless `DAL_AUTO_EXECUTION=true`

---

## Execution Modes

| Mode | Behavior |
|------|----------|
| `MANUAL` | Suggestion returned, no execution |
| `SEMI_AUTOMATIC` | Requires human approval via `/api/actions/approve/` |
| `AUTOMATIC` | Executes if guards pass and auto mode enabled |

---

## Safety Guardrails

| Rule | Effect |
|------|--------|
| Destructive actions | Always require approval |
| Bulk > 5 cards | Blocked until approved |
| `DAL_AUTO_EXECUTION=false` | Blocks all AUTOMATIC mode |
| Hourly rate limit | Default 10 auto actions/hour |
| Loop detection | Same card+action within 300s cooldown blocked |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/actions/` | Overview |
| GET | `/api/actions/queue/` | Pending decision queue |
| POST | `/api/actions/generate/` | Generate decisions from output |
| POST | `/api/actions/execute/` | Execute action (or get approval prompt) |
| POST | `/api/actions/approve/` | Approve + execute |
| POST | `/api/actions/reject/` | Reject action |
| GET | `/api/actions/decisions/{id}/` | Decision detail |

Also available under `/api/v1/actions/`.

---

## Persistence

| Table | Purpose |
|-------|---------|
| `decision_records` | Decision queue with retry/DLQ |
| `action_execution_log` | Full execution audit trail |

---

## ODTL Integration

Each action records in trace via `TraceCollector.record_action()` → `actions_taken[]` in decision trace.

Fields: `decision_id`, `action_type`, `trace_id`, `effect`, execution metadata.

---

## EOR Pipeline Integration

After semantic layer in `execute_eql_query()`:

```python
output = enrich_with_decisions(output, source_trace_id=collector.trace_id)
# output["decisions"], output["action_queue"], output["decision_summary"]
```

No auto-execution in query pipeline — actions require explicit API call.

---

## Environment Variables

```env
DAL_AUTO_EXECUTION=false
DAL_MAX_AUTO_ACTIONS_PER_HOUR=10
DAL_ACTION_COOLDOWN_SECONDS=300
```

Trello write operations require `TRELLO_API_KEY` and `TRELLO_API_TOKEN`.

---

## Tests

```bash
python manage.py test apps.intelligence.tests.decision_action
```

Covers: action generation, prioritization, guards, approval, feedback, Trello dry-run, orchestrator, API, runner integration.
