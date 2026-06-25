# ECP — Evolution Control Plane

The Evolution Control Plane (ECP) governs safe system evolution across all EOR layers: EQL, Query Engine, Semantic Layer, CMGL, Metrics, and ODTL.

## Purpose

Without controlled evolution, any change to language syntax, semantic taxonomy, or metrics can break existing queries, dashboards, and downstream integrations. ECP ensures:

- Every layer is versioned
- Backward compatibility is explicit (OK / WARN / BREAK)
- Legacy queries are adapted automatically
- Impact is simulated before deployment
- Rollback is auditable
- Safe Mode blocks high-risk changes

## Architecture

```
Change Request
      │
      ▼
┌─────────────────┐
│ Versioning Core │  SYSTEM_VERSION + per-layer versions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Compatibility   │  Matrix: OK / WARN / BREAK per layer
│ Matrix Engine   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Impact Analyzer │  affected_queries, metrics, risk_level
└────────┬────────┘
         │
    SAFE_MODE? ──HIGH risk──► REJECT + audit log
         │
         ▼
┌─────────────────┐
│ Feature Flags   │  Gradual rollout of new parsers/engines
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Migration       │  Query adapter + semantic entity migration
│ Pipeline        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Rollback        │  Restore prior version snapshot
│ + Audit Log     │  evolution_log table
└─────────────────┘
```

## Module Layout

```
apps/intelligence/services/evolution/
├── versioning/core.py          # SYSTEM_VERSION, layer versions
├── compatibility/
│   ├── matrix.py               # Compatibility matrix engine
│   └── query_adapter.py        # Legacy EQL → modern EQL
├── semantic_migration.py       # Entity/metric taxonomy migration
├── impact_analyzer.py          # Pre-deploy impact simulation
├── feature_flags/flags.py      # Controlled feature rollout
├── rollback/manager.py         # Version rollback snapshots
├── pipeline/orchestrator.py    # Full deployment pipeline
├── storage.py                  # evolution_log persistence
└── config.py                   # EOR_SAFE_MODE
```

## Versioning

| Constant | Default | Description |
|----------|---------|-------------|
| `SYSTEM_VERSION` | 1.0.0 | Global system version |
| `EQL_VERSION` | 1.1.0 | Query language |
| `QUERY_ENGINE_VERSION` | 1.1.0 | Compilation/execution |
| `SEMANTIC_LAYER_VERSION` | 1.0.0 | Business semantics |
| `CMGL_VERSION` | 1.1.0 | Model governance |
| `METRICS_VERSION` | 1.1.0 | Metric definitions |
| `ODTL_VERSION` | 1.0.0 | Observability |

Override system version via `EOR_SYSTEM_VERSION` environment variable.

## Compatibility Matrix

Each layer defines transitions between versions:

| Level | Meaning |
|-------|---------|
| OK | Fully compatible |
| WARN | Compatible with adapter/migration |
| BREAK | Breaking change — requires explicit approval |

Example: EQL `1.0.0 → 2.0.0` = BREAK; Metrics `1.0.0 → 1.1.0` = WARN.

## Query Backward Compatibility

Legacy syntax is detected and adapted before parsing:

| Legacy | Modern |
|--------|--------|
| `RISK = HIGH` | `RISK_SCORE >= 50` |
| `FAILURE_RATE` | `INCIDENT_RATE` |
| `TASK_COMPLETION` | `DELIVERY` |

The adapter runs in `execute_eql_query()` via `prepare_query_for_execution()`. Evolution metadata is returned in `result["evolution"]`.

## Semantic Migration

Entities are migrated after the semantic layer:

- `FAILURE` → `INCIDENT`
- `TASK_COMPLETION` → `DELIVERY`
- `INCIDENT` → `RISK_EVENT` (when risk_score ≥ 75 + external_dependency)

## Safe Deployment Mode

Set `EOR_SAFE_MODE=true` to block HIGH-risk changes in the pipeline. All changes still pass through impact analysis and are logged to `evolution_log`.

## Feature Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `FEATURE_NEW_EQL_PARSER` | false | New parser rollout |
| `FEATURE_NEW_SEMANTIC_MAPPER` | false | New semantic mapper |
| `FEATURE_NEW_METRICS_ENGINE` | false | New metrics engine |
| `FEATURE_QCL_COMPILER` | true | QCL compilation |
| `FEATURE_SEMANTIC_LAYER` | true | BSL enrichment |
| `FEATURE_CMGL_ENFORCEMENT` | true | Governance enforcement |
| `FEATURE_ODTL_TRACING` | true | Decision tracing |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/evolution/` | Overview |
| GET | `/api/evolution/version/` | Version snapshot + compatibility |
| POST | `/api/evolution/impact/` | Impact analysis or query adaptation |
| POST | `/api/evolution/pipeline/` | Full deployment pipeline |
| GET | `/api/evolution/flags/` | Feature flags |
| GET/POST | `/api/evolution/rollback/` | List targets / execute rollback |
| GET | `/api/evolution/history/` | Audit log |

Also available under `/api/v1/evolution/`.

## Audit Log

Table: `evolution_log`

| Field | Description |
|-------|-------------|
| version_from | Source version |
| version_to | Target version |
| change_type | upgrade, rollback, patch, etc. |
| affected_layers | JSON list of layers |
| risk_assessment | Full impact output |
| status | pending, approved, rejected, completed |
| timestamp | created_at |

## Pipeline Flow

1. **Detect** — identify change type and versions
2. **Validate** — check compatibility matrix
3. **Simulate** — run impact analyzer on sample queries/metrics
4. **Approve/Reject** — safe mode gate for HIGH risk
5. **Audit** — persist to evolution_log
6. **Monitor** — (production) observe via ODTL traces
7. **Confirm/Rollback** — rollback_to_version() if needed

## Integration with Query Pipeline

```
EQL input
  → prepare_query_for_execution()   [ECP: adapt legacy]
  → parse → validate → compile → execute
  → apply_semantic_layer()
  → migrate_entities()              [ECP: semantic migration]
  → output["evolution"]             [ECP: version metadata]
```

## Environment Variables

```env
EOR_SAFE_MODE=false
EOR_SYSTEM_VERSION=1.0.0
FEATURE_NEW_EQL_PARSER=false
```

## Tests

```bash
python manage.py test apps.intelligence.tests.evolution
```

Covers: compatibility matrix, query adapter, semantic migration, impact analysis, rollback, safe mode, audit log, API, and runner integration.
