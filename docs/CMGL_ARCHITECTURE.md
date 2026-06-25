# Core Model Governance Layer (CMGL) — Architecture

**Version:** 1.0  
**Model Version:** 1.1

---

## Purpose

CMGL is the **single source of semantic truth** for EOR. It prevents each layer from interpreting business concepts differently by enforcing:

- Canonical domain models (CDM)
- Global registry of entities, metrics, and events
- Cross-layer validation
- Semantic consistency checks
- Controlled model versioning

---

## Pipeline Integration

```
EQL → [CMGL: enforce AST] → Query Engine → [CMGL: enforce plan]
    → Semantic Layer → [CMGL: govern output] → Report
```

---

## Canonical Domain Model (CDM)

| Type | Description |
|------|-------------|
| `WorkItem` | Operational work unit (card, event, enrichment) |
| `WorkEvent` | Timeline event |
| `WorkEntity` | Business entity (Incident, Delivery, Project…) |
| `WorkMetric` | Canonical metric definition |
| `WorkRelationship` | Entity relationships |

---

## Modules

| Module | Path | Role |
|--------|------|------|
| Registry | `core_model/registry.py` | Entity types, metrics, events, aliases |
| Dictionary | `core_model/dictionary.py` | Global semantic definitions |
| Validator | `core_model/validator.py` | Cross-layer validation |
| Consistency | `core_model/semantic_consistency.py` | Conflict detection |
| Versioning | `core_model/versioning.py` | Model version compatibility |
| Enforcer | `core_model/enforcer.py` | Block invalid constructs |

---

## Rules

1. No layer may invent unregistered entities or metrics
2. All derived entities must map to CDM
3. Extensions must be registered via `registry.register_extension()`
4. Model changes require version bump in `versioning.py`

---

## Error Codes

| Code | Meaning |
|------|---------|
| `UNREGISTERED_ENTITY` | Entity type not in registry |
| `UNREGISTERED_METRIC` | Metric not in registry |
| `UNREGISTERED_EVENT` | Event type not in registry |
| `SEMANTIC_INCONSISTENCY` | Conflicting definitions detected |
| `CROSS_LAYER_VALIDATION` | Layer output inconsistent with CDM |
| `MODEL_VERSION_ERROR` | Version incompatibility |

---

## API Response

Reports now include a `governance` block:

```json
{
  "governance": {
    "model_version": "1.1",
    "governed": true,
    "cross_layer_validation": {"valid": true},
    "semantic_consistency": {"consistent": true, "conflicts": []}
  }
}
```
