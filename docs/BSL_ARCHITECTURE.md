# Business Semantic Layer (BSL) — Architecture

**Version:** 1.0  
**Status:** Implemented

---

## Purpose

Transform technical query results (cards, events, labels) into **business entities** and **operational KPIs** that match how users think: projects, incidents, deliveries, risks, bottlenecks, SLA.

---

## Pipeline

```
EQL (incl. semantic filters)
    ↓
Semantic Query Resolver  →  technical filters for Query Engine
    ↓
Query Engine (Compiler → Optimizer → Guard → Executor)
    ↓
Raw Execution Result
    ↓
Business Semantic Layer (BSL)
    ├── Entity Mapper
    ├── Semantic Enrichment
    ├── Business Metrics
    └── Domain Intelligence
    ↓
Enriched Report Output
```

---

## Separation of Responsibilities

| Layer | Responsibility | Must NOT |
|-------|----------------|----------|
| **Query Engine** | Execute data queries | Understand business concepts |
| **Semantic Query Resolver** | Translate semantic EQL → technical filters | Execute queries or map entities |
| **Semantic Layer** | Map, classify, metrics, insights | Execute SQL/queries |

---

## Business Entities

| Entity | Description |
|--------|-------------|
| `Project` | Group of related cards by prefix/category |
| `Initiative` | Strategic work stream |
| `TaskGroup` | Cluster of operational tasks |
| `Incident` | Delay, error, block, rework |
| `Delivery` | Completion, deploy, send |
| `RiskEvent` | Dependency, recurring delay, overload |
| `Bottleneck` | Stagnation or excessive movement |
| `SLAContract` | Due-date commitment unit |
| `WorkloadUnit` | Member assignment load |

---

## Semantic EQL Filters

```eql
FILTER:
PERIOD = LAST_30_DAYS
ENTITY_TYPE = INCIDENT
CATEGORY = FINANCEIRO
RISK_LEVEL >= HIGH
ENTITY_STATUS = ACTIVE
LIMIT:
100
```

| Semantic Field | Maps To |
|----------------|---------|
| `ENTITY_TYPE` | Classification rules (incident/delivery/project) |
| `CATEGORY` | Title prefix / label area |
| `RISK_LEVEL` | Risk score thresholds |
| `ENTITY_STATUS` | ACTIVE, COMPLETED, DELAYED, BLOCKED |

---

## Business KPIs

- Incident Rate
- Delivery Success Rate
- Risk Exposure Index
- Team Load Balance Score
- Operational Efficiency Index
- Bottleneck Density
- SLA Breach Probability

---

## Cache

Table: `semantic_entity_cache` — stores inferred entity classifications per card to avoid re-computation.

---

## Example Questions Answered

- *"Quais incidentes financeiros nos últimos 30 dias?"* → `ENTITY_TYPE=INCIDENT`, `CATEGORY=FINANCEIRO`, `PERIOD=LAST_30_DAYS`
- *"Qual área gera mais risco?"* → Domain intelligence by category
- *"Onde estão os gargalos?"* → Bottleneck entities + density metric
- *"Qual tipo de entrega falha mais?"* → Delivery success rate by category
