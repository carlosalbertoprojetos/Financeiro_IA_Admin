# Test Coverage Report — EOR Intelligence

**Date:** 2026-06-20  
**Command:** `coverage run --source=apps/intelligence manage.py test apps.intelligence.tests`  
**Scope:** `apps/intelligence`

---

## Summary

| Metric | Value | Sprint 1 Target |
|--------|-------|-----------------|
| Tests executed | 330 | 271+ (suite grew with DAL/OLE/BVE) |
| Tests passed | **330 / 330** | 100% |
| Tests skipped | 0 | 0 |
| Tests xfail | 0 | 0 |
| **Line coverage** | **90%** (8548 stmts, 885 miss) | ≥ 90% |

---

## Critical Modules (Target ≥ 90%)

| Module | Coverage | Status |
|--------|----------|--------|
| `eql/parser.py` | 94% | OK |
| `eql/validator.py` | 96% | OK |
| `query_engine/runner.py` | 89% | Near target |
| `query_engine/compiler/compiler.py` | 98% | OK |
| `semantic_layer/pipeline.py` | 100% | OK |
| `core_model/registry.py` | 98% | OK |
| `observability/*` (tested paths) | 90%+ | OK |
| `decision_layer/orchestrator.py` | **95%** | OK |
| `decision_layer/trello_executor.py` | **100%** | OK |
| `decision_layer/queue/manager.py` | **98%** | OK |
| `business_value/pipeline.py` | **90%** | OK |
| `business_value/config.py` | **100%** | OK |
| `views_actions.py` | **85%** | Near target |

---

## Modules Below 80%

| Module | Coverage | Risk |
|--------|----------|------|
| `management/commands/report_query.py` | 0% | Low (CLI only) |
| `query_engine/planner.py` | 0% | Medium (legacy/unused?) |
| `report_query/diagnose.py` | 0% | Low (CLI) |
| `report_query/presets.py` | 0% | Low |
| `providers/trello.py` | 40% | Medium |
| `decision_layer/trello_executor.py` | 31% | **High** (production writes) |
| `decision_layer/orchestrator.py` | 56% | **High** |
| `decision_layer/queue/manager.py` | 47% | **High** |
| `views_actions.py` | 51% | Medium |
| `decision_layer/guards/rules.py` | 65% | Medium |
| `business_value/config.py` | 63% | Medium |
| `report_query/domain/dsl_parser.py` | 68% | Medium |
| `risk_engine/scorer.py` | 71% | Medium |
| `report_query/templates/sla.py` | 71% | Low |
| `semantic_layer/enrichment.py` | 74% | Medium |
| `core_model/validator.py` | 74% | Medium |

---

## Correction Plan (to reach 90%)

### Priority 1 — Production-critical (~160 statements)

1. **`decision_layer/orchestrator.py`** — tests for EXECUTED, FAILED, BLOCKED, PENDING_APPROVAL, Trello dispatch paths (mock client).
2. **`decision_layer/trello_executor.py`** — mock `TrelloClient` for ADD_COMMENT, ESCALATE, REOPEN.
3. **`decision_layer/queue/manager.py`** — retry, dead-letter, mark_executed flows.

### Priority 2 — API layer (~50 statements)

4. **`views_actions.py`** — approve/reject/execute error paths.

### Priority 3 — Guards & config (~30 statements)

5. **`guards/rules.py`** — rate limit, loop detection, auto-disabled env paths.
6. **`business_value/config.py`** — env override parsing.

### Estimated effort

~4–6 hours of focused tests → projected **90–91%** coverage.

---

## Notes

- Test files themselves show 100% coverage (expected).
- Coverage excludes untested CLI commands by design; consider smoke tests or mark as non-critical.
- No tests use `@skip`, `@xfail`, or artificial mocks for the fixed `test_get_query_info`.
