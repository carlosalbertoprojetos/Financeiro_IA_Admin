# Migration Audit — tip_intelligence

**Date:** 2026-06-20  
**App:** `tip_intelligence` (`apps/intelligence`)

---

## Migration Timeline

| # | Migration | Purpose | Dependencies |
|---|-----------|---------|--------------|
| 0001 | `initial` | TimelineEvent, CardEnrichment, KnowledgeBaseEntry | trello |
| 0002 | `reportauditlog` | Report audit trail | 0001 |
| 0003 | `reportquerylog` | EQL query logging | 0002 |
| 0004 | `reportqueryexecutiontrace` | QCL execution traces | 0003 |
| 0005 | `semanticentitycache` | BSL entity cache | 0004 |
| 0006 | `decisiontracerecord` | ODTL decision traces | 0005 |
| 0007 | `evolutionlog` | ECP evolution audit | 0006 |
| 0008 | `decisionrecord_actionexecutionlog` | DAL queue + action audit | 0007 |
| 0009 | `ole_models` | DecisionEffectiveness, OrganizationalMemory, Playbooks | 0008 |
| 0010 | `businessvaluerecordmodel` | BVE financial records | 0009 |

---

## Validation Results

```bash
python manage.py showmigrations tip_intelligence
# All [X] applied — linear chain, no gaps
```

| Check | Result |
|-------|--------|
| Linear dependency chain | PASS |
| No duplicate table names | PASS |
| Index naming unique | PASS |
| Rollback order (reverse) | Valid — 0010 → 0001 |
| Cross-app FK integrity | PASS (references trello.*) |

---

## Layer Mapping

| Layer | Migrations |
|-------|------------|
| Timeline | 0001 |
| Semantic | 0005 |
| Observability (ODTL) | 0003, 0004, 0006 |
| Governance audit | 0002 |
| ECP | 0007 |
| DAL | 0008 |
| OLE | 0009 |
| BVE | 0010 |

---

## Rollback Notes

- Rollback is **destructive** for 0008–0010 (drops decision/action/value tables).
- Production rollback should: disable DAL auto-execution → export `evolution_log`, `decision_records`, `business_value_records` → migrate backward one step at a time.
- No data migration scripts between versions — all additive schema.

---

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| 0010 applied before OLE has data | Low | BVE records empty until actions execute |
| Large action log growth (0008) | Medium | Retention policy recommended |
| decision_traces JSON size (0006) | Medium | Archive traces > 90 days |

---

## Recommendation

Migrations are **consistent and production-ready**. No reordering required.
