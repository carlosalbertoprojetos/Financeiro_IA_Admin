# Root Cause Analysis — `test_get_query_info`

**Date:** 2026-06-20  
**Test:** `apps.intelligence.tests.test_report_query.ReportQueryAPITests.test_get_query_info`  
**Status:** RESOLVED

---

## Symptom

```
AssertionError: 'report_types' not found in { 'endpoint': 'POST /api/reports/query/', ... }
```

The test expected `report_types` in the GET `/api/reports/query/` response, but the endpoint returned only metadata (`endpoint`, `description`, `supports_dsl`, `example_json`, `example_dsl`).

---

## Root Cause

The GET handler in `apps/intelligence/views_report_query.py` was implemented as API documentation only. It never exposed the list of supported report templates, even though:

1. The test contract assumed discovery metadata including `report_types`.
2. `ReportTemplate` enum already defines all valid report types in `apps/intelligence/services/report_query/domain/filters.py`.

This was a **contract drift** between the view and the test — not a flaky test or environment issue.

---

## Correction Applied

Added `report_types` to the GET response, derived directly from `ReportTemplate` enum (single source of truth):

```python
"report_types": [
    {"value": t.value, "label": t.value.title()}
    for t in ReportTemplate
],
```

File modified: `apps/intelligence/views_report_query.py`

---

## Evidence

```bash
python manage.py test apps.intelligence.tests.test_report_query.ReportQueryAPITests.test_get_query_info -v 2
# Result: OK

python manage.py test apps.intelligence.tests -v 1
# Result: Ran 290 tests — OK
```

---

## Impact

| Area | Impact |
|------|--------|
| API consumers | GET `/api/reports/query/` now exposes discoverable report types |
| Backward compatibility | Additive only — no breaking changes |
| POST behavior | Unchanged |
| Test suite | Last known failure eliminated |

---

## Prevention

- GET discovery endpoints should stay aligned with domain enums used by POST validation.
- When adding API metadata tests, ensure the view reads from the same enum/registry as payload validation.
