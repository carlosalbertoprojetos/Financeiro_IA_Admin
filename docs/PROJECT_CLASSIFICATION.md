# PROJECT CLASSIFICATION — TIP (Trello Intelligence Platform)

**Versão:** 2.0  
**Data:** 2026-06-19  
**Base auditada:** `EOP/` (Executive Operation Report)  
**Política de recuperação:** não apagar, não reescrever módulos existentes, não remover código, manter compatibilidade de APIs.

---

## 1. Resumo executivo

A base atual é um **MVP operacional em transição para produto comercial TIP**, com **duas camadas backend coexistindo**:

| Camada | Prefixo | Papel |
|--------|---------|-------|
| **Legacy** | `/api/dashboard/`, `/api/analytics/`, `/api/integrations/trello/` | Ingestão Trello ORM, engine métricas Kanban, PDF, AI |
| **TIP Platform (`apps/`)** | `/api/v1/` | Facades, Integration Engine, tasks canônicas, auth/navegação placeholder |

O frontend evoluiu de página única para **shell Next.js** com 6 rotas; **Dashboard v1** e **Integrações Trello** são funcionais; Analytics, Reports e Settings permanecem placeholder.

Não existem serializers DRF — views retornam `Response` com dicts.

### Legenda de categorias

| Categoria | Significado |
|-----------|-------------|
| **CORE MVP** | Essencial para produto comercial (Trello + Excel) |
| **FUTURE MVP** | Valor incremental pós-MVP; arquitetura preparada |
| **ENTERPRISE** | Financeiro/executivo avançado; fora do MVP TIP |
| **CONGELADO** | Existe; mantido intacto na recuperação |
| **OUT OF SCOPE** | Sem aderência ao produto TIP |

### Legenda de status

| Status | Significado |
|--------|-------------|
| ✅ Implementado | Código funcional |
| ⚠️ Parcial | Existe mas incompleto ou sem UI completa |
| ❌ Planejado | Não existe |
| 🔒 Congelado | Não alterar na fase de recuperação |

---

## 2. Inventário de módulos

### 2.1 Infraestrutura — `tip_backend/`

| Item | Arquivos | APIs | Models | Services | Views | Testes |
|------|----------|------|--------|----------|-------|--------|
| Config Django | `settings/base.py`, `dev.py`, `prod.py` | — | — | — | — | — |
| Rotas globais | `urls.py` | 7 prefixos + admin + health | — | — | — | — |
| Celery | `celery.py` | — | — | — | — | — |

| Classificação | **CONGELADO** (infra) · Celery tasks: **FUTURE MVP** |
| Justificativa | Infra estável; Celery bootstrap existe, tasks parciais em `apps.integrations.tasks` |
| Reaproveitamento | 100% |
| Status | ✅ 🔒 |

**Dependências:** Django, python-dotenv, celery, redis, corsheaders

---

### 2.2 Core — `core/`

| Item | Arquivos | APIs | Models | Services | Views | Testes |
|------|----------|------|--------|----------|-------|--------|
| Health | `views.py`, `urls.py` | `GET /health/` | — | — | `HealthCheckView` | ❌ |
| Base model | `models.py` | — | `TimeStampedModel` | — | — | — |
| Tenant | `migrations/0001_initial.py` | — | `Tenant`, `TenantMembership` (migration only) | — | — | — |

| Classificação | Health: **CORE MVP** · Tenant: **ENTERPRISE** + **CONGELADO** |
| Status | Health ✅ · Tenant ⚠️ orphan 🔒 |

---

### 2.3 Legacy Trello — `integrations/trello/`

| Item | Arquivos | APIs | Models | Services | Views | Testes |
|------|----------|------|--------|----------|-------|--------|
| Cliente HTTP | `client.py` | — | — | `TrelloClient` | — | ❌ |
| Sync | `services/sync.py` | — | — | `sync_board()` | — | ❌ |
| Normalizers | `normalizers.py` | — | — | card/list mappers | — | ❌ |
| Models ORM | `models.py` | — | `Board`, `BoardList`, `Member`, `Card`, `Action`, `CardStatusHistory`, `EntityHistory`, `Snapshot` | — | — | — |
| API sync | `views.py`, `urls.py` | `POST /api/integrations/trello/sync/<board_id>/` | — | sync_board | `SyncBoardView` | ❌ |
| CLI | `management/commands/sync_trello_board.py` | — | — | sync_board | — | ❌ |

| Classificação | Sync/Client/Models: **CORE MVP** · EntityHistory/Snapshot: **CONGELADO** |
| Justificativa | Caminho legacy ainda ativo; alimenta analytics/dashboard/reports/ai |
| Reaproveitamento | 95% — manter; TIP usa camada paralela `apps/integrations` |
| Status | ✅ 🔒 (não reescrever) |

**APIs adicionais (via data-sources):** `POST /api/v1/data-sources/trello/sync/<board_id>/`

---

### 2.4 Platform Integration Engine — `apps/integrations/`

| Item | Arquivos | APIs | Models | Services | Views | Testes |
|------|----------|------|--------|----------|-------|--------|
| Models | `models.py` | — | `IntegrationConnection`, `CanonicalTaskRecord`, `IntegrationState`, `IngestionQueueEvent` | — | — | — |
| SyncEngine | `core/engine.py` | — | — | sync full | — | ✅ test_engine |
| IngestionEngine | `core/ingestion_engine.py` | — | — | sync incremental | — | ✅ test_ingestion_engine |
| Registry | `core/registry.py` | — | — | trello/jira/clickup | — | ✅ |
| Adapters | `trello/adapter.py`, `adapters/jira.py`, `adapters/clickup.py` | — | — | BaseIntegrationAdapter | — | ✅ |
| Trello client | `trello/client.py`, `mapper.py`, `incremental.py`, `connections.py` | — | — | fetch_incremental | — | ✅ |
| State store | `core/state_store.py` | — | — | get_last_cursor, update_cursor | — | ✅ |
| Queue | `core/queue.py` | — | — | publish/consume multi-backend | — | ✅ test_queue |
| Workers | `workers/trello_worker.py` | — | — | consume queue → persist | — | ✅ test_trello_worker |
| Celery tasks | `tasks.py` | — | — | dispatch_integration_event | — | ❌ |
| Data-sources API | via `apps/data_sources/trello_views.py` | connect/sync/status | — | SyncEngine | — | ✅ |
| Integrations API | `trello/views.py`, `urls.py` | connect/workspaces/boards/sync | — | SyncEngine | — | ✅ |

**APIs TIP (`/api/v1/`):**

| Método | Path |
|--------|------|
| POST | `/api/v1/data-sources/trello/connect/` |
| POST | `/api/v1/data-sources/trello/sync/` |
| GET | `/api/v1/data-sources/trello/status/` |
| POST | `/api/v1/integrations/trello/connect/` |
| GET | `/api/v1/integrations/trello/connections/<id>/workspaces/` |
| GET | `/api/v1/integrations/trello/connections/<id>/boards/` |
| POST | `/api/v1/integrations/trello/connections/<id>/sync/` |

| Classificação | Engine + Trello adapter: **CORE MVP** · Jira/ClickUp stubs: **FUTURE MVP** · Queue/Celery: **FUTURE MVP** |
| Justificativa | Caminho canônico para multi-provider; Trello funcional; outros registrados |
| Reaproveitamento | 100% engine; legacy sync permanece paralelo |
| Status | ✅ Trello · ⚠️ Jira/ClickUp placeholder |

**Dependências:** `core.TimeStampedModel`, `apps.dashboards.canonical_metrics`, Celery (opcional), cryptography (credenciais)

---

### 2.5 Excel — `integrations/excel/` (planejado)

| Item | Status |
|------|--------|
| Módulo Django | ❌ |
| API placeholder | `GET|POST /api/v1/data-sources/excel/` → 501 |

| Classificação | **CORE MVP** (criar módulo novo) |
| Reaproveitamento | Adapter → `CanonicalTask` ou `CardRecord` |
| Status | ❌ Planejado |

---

### 2.6 Integrações futuras — Jira, ClickUp, Monday, CSV

| Item | Base | Classificação |
|------|------|---------------|
| Jira | `apps/integrations/adapters/jira.py` (stub) | **FUTURE MVP** |
| ClickUp | `apps/integrations/adapters/clickup.py` (stub) | **FUTURE MVP** |
| Monday | — | **FUTURE MVP** |
| CSV | — | **FUTURE MVP** |

---

### 2.7 Legacy Analytics — `analytics/`

| Item | Arquivos | APIs | Services | Testes |
|------|----------|------|----------|--------|
| Engine | `engine/metrics.py`, `types.py` | — | lead/cycle/throughput/aging/delay/rework | ✅ test_metrics |
| Adapters | `adapters.py` | — | `load_board_records()` | ❌ |
| Builders | `services/builders.py` | — | overview/team/cards/gaps | ✅ test_builders |
| Views | `views.py`, `urls.py` | 5 endpoints `/api/analytics/metrics/*` | — | ❌ |

| Classificação | Engine + builders: **CORE MVP** · team/gaps UI: **FUTURE MVP** |
| Reaproveitamento | 100% engine; alimentado por legacy Trello ORM |
| Status | ✅ backend · ⚠️ UI placeholder |

**Dependências:** `integrations.trello.models`

---

### 2.8 Platform Analytics — `apps/analytics/`

| Item | Arquivos | APIs | Testes |
|------|----------|------|--------|
| Facade | `views.py`, `urls.py` | `GET /api/v1/analytics/` + include legacy | ❌ |

| Classificação | **CORE MVP** (facade) · **CONGELADO** (delegação) |
| Status | ✅ facade |

---

### 2.9 Legacy Dashboard — `dashboard/`

| Item | Arquivos | APIs | Services | Testes |
|------|----------|------|----------|--------|
| Builders | `services/builders.py` | — | overview/productivity/efficiency/bottlenecks | ✅ test_builders |
| Views | `views.py`, `urls.py` | 4 endpoints `/api/dashboard/*` | — | ❌ |

| Classificação | **CORE MVP** (legacy path) · builders: **CONGELADO** |
| Status | ✅ 🔒 |

---

### 2.10 Platform Dashboards — `apps/dashboards/`

| Item | Arquivos | APIs | Services | Testes |
|------|----------|------|----------|--------|
| Canonical metrics | `services/canonical_metrics.py` | `GET /api/v1/dashboards/metrics/` | tasks_by_status, overdue, provider, trend_7d | ✅ 6 tests |
| Views | `views.py`, `urls.py` | module metadata | — | ✅ |

| Classificação | **CORE MVP** (novo caminho canônico) |
| Justificativa | Dashboard frontend consome este endpoint |
| Reaproveitamento | 100%; lê `CanonicalTaskRecord` |
| Status | ✅ |

**Dependências:** `apps.integrations.models.CanonicalTaskRecord`

---

### 2.11 Legacy Reports — `reports/`

| Item | Arquivos | APIs | Services | Testes |
|------|----------|------|----------|--------|
| PDF | `engine/pdf_builder.py`, `charts.py` | `POST /api/reports/executive/` | build_executive_report_pdf | ✅ test_pdf_builder |
| Views | `views.py`, `urls.py` | — | — | ❌ |

| Classificação | **CORE MVP** |
| Status | ✅ backend · ❌ UI funcional |

---

### 2.12 Platform Reports — `apps/reports/`

| Classificação | **CORE MVP** (facade) |
| APIs | `GET /api/v1/reports/` · `POST /api/v1/reports/executive/` (delega legacy) |
| Status | ✅ facade · ❌ UI |

---

### 2.13 Legacy AI — `ai/`

| Item | Arquivos | APIs | Services | Testes |
|------|----------|------|----------|--------|
| Analyst | `analyst.py` | `POST /api/ai/analyze/` | analyze_metrics | ✅ test_analyst |
| Views | `views.py`, `urls.py` | — | — | ❌ |

| Classificação | **CORE MVP** (análise operacional, não financeira) |
| Status | ✅ · ❌ UI |

---

### 2.14 Platform AI — `apps/ai_insights/`

| Classificação | **CORE MVP** (facade) |
| APIs | `GET /api/v1/ai-insights/` · `POST /api/v1/ai-insights/analyze/` |
| Status | ✅ facade · ❌ UI |

---

### 2.15 Data Sources — `apps/data_sources/`

| Item | Arquivos | APIs | Testes |
|------|----------|------|--------|
| Overview | `views.py` | `GET /api/v1/data-sources/` | ❌ |
| Trello | `trello_views.py` | connect/sync/status | ✅ test_trello_endpoints |
| Excel | `views.py` | placeholder 501 | ❌ |

| Classificação | Trello endpoints: **CORE MVP** · Excel: **CORE MVP** (placeholder) |
| Status | ✅ Trello · ❌ Excel |

---

### 2.16 Users — `apps/users/`

| APIs | `POST login/` · `POST logout/` · `GET me/` · `GET permissions/` |
| Classificação | **FUTURE MVP** (auth demo, não produção) |
| Status | ⚠️ placeholder localStorage |

---

### 2.17 Settings — `apps/settings/`

| APIs | `GET /api/v1/settings/` · `GET navigation/` |
| Classificação | **FUTURE MVP** |
| Status | ⚠️ placeholder |

---

### 2.18 Exports — `apps/exports/`

| APIs | `GET /api/v1/exports/` · `GET pdf/` (metadata) |
| Classificação | **CORE MVP** (catálogo) · PDF real via reports |
| Status | ⚠️ metadata only |

---

### 2.19 Platform root — `apps/`

| Arquivos | `urls.py`, `platform_views.py`, `permissions.py`, `interfaces.py` |
| APIs | `GET /api/v1/` |
| Classificação | **CORE MVP** (shell API) |
| Status | ✅ |

---

### 2.20 Frontend — `frontend/`

| Rota | Feature | Status | APIs consumidas |
|------|---------|--------|-----------------|
| `/login` | Auth demo | ✅ | `POST /api/v1/users/login/` |
| `/dashboard` | Dashboard v1 canônico | ✅ | `GET /api/v1/dashboards/metrics/` |
| `/integrations` | Trello connect/sync/status | ✅ | data-sources/trello/* |
| `/analytics` | Placeholder | ⚠️ | documentado, não consome |
| `/reports` | Placeholder | ⚠️ | documentado, não consome |
| `/settings` | Placeholder | ⚠️ | — |

**Componentes legacy (não wired):** `components/FilterBar.tsx`, `KpiGrid.tsx`, `DashboardCharts.tsx` → `/api/dashboard/*`

| Classificação | Shell + dashboard v1 + integrations: **CORE MVP** · placeholders: **CORE MVP** (completar) · legacy components: **CONGELADO** |
| Reaproveitamento | 40% funcional; legacy stack preservado para migração gradual |
| Status | ⚠️ Parcial |

---

### 2.21 ENTERPRISE (não existem no código)

| Conceito | Classificação |
|----------|---------------|
| CFO Virtual, Forecast, Recovery, Business Value, ROI | **ENTERPRISE** / **OUT OF SCOPE** |
| Executive Board financeiro, Financial Health | **ENTERPRISE** |
| RBAC multi-tenant (Tenant migration) | **ENTERPRISE** + **CONGELADO** |
| Pilot Readiness checklist | **ENTERPRISE** |

---

### 2.22 FUTURE MVP

| Item | Base existente |
|------|----------------|
| Comparativos / benchmarking | Snapshots, `build_team()` |
| Alertas automáticos | — |
| Filtros server-side | cards API |
| Celery sync assíncrono | `celery.py`, queue backends |
| CSV / Jira / ClickUp / Monday | adapter stubs |
| Dashboard legacy + canonical unificado | dois data planes |
| Auth produção (JWT/session) | users placeholder |
| Worker pipeline completo | trello_worker parcial |

---

### 2.23 Infra suporte

| Item | Classificação | Status |
|------|---------------|--------|
| `docker-compose.yml` | CORE MVP | ✅ |
| `requirements.txt` | CORE MVP | ✅ |
| `.env` / `.env.example` | CORE MVP | ✅ |
| `Executar_EOR.bat` | CORE MVP | ✅ |
| `README.md` | CONGELADO | ⚠️ desatualizado |
| `docs/TIP_*.md` | CORE MVP | ✅ |

---

## 3. Matriz consolidada

| Módulo | Categoria | Status | Reaproveitamento | Ação |
|--------|-----------|--------|------------------|------|
| `integrations/trello` (legacy) | CORE MVP + CONGELADO | ✅ | 95% | Manter |
| `apps/integrations` (engine) | CORE MVP | ✅ Trello | 100% | Estender Excel |
| `apps/data_sources` Trello | CORE MVP | ✅ | 100% | Manter |
| `apps/dashboards` canonical | CORE MVP | ✅ | 100% | Manter |
| `analytics/engine` | CORE MVP | ✅ | 100% | Manter |
| `dashboard/` legacy | CORE MVP + CONGELADO | ✅ | 100% | Não reescrever |
| `reports/engine` | CORE MVP | ✅ | 95% | UI Sprint 04 |
| `ai/analyst` | CORE MVP | ✅ | 90% | UI Sprint 04 |
| `integrations/excel` | CORE MVP | ❌ | — | Sprint 03 |
| Frontend shell | CORE MVP | ⚠️ 40% | 70% | Sprints 02–04 |
| `apps/users/settings` | FUTURE MVP | ⚠️ | 50% | Pós-MVP |
| Jira/ClickUp/Monday | FUTURE MVP | stub | — | Pós-MVP |
| Tenant migration | ENTERPRISE + CONGELADO | ⚠️ | 20% | Não tocar |
| CFO/Forecast/ROI | OUT OF SCOPE | ❌ | 0% | Não implementar |

---

## 4. Dois planos de dados (dual data plane)

```
CAMINHO LEGACY                          CAMINHO TIP (canônico)
─────────────────                       ──────────────────────
TrelloClient (legacy)                   TrelloClient (apps)
       │                                       │
sync_board()                            SyncEngine / IngestionEngine
       │                                       │
integrations.trello.models              CanonicalTaskRecord
(Board, Card, Action...)                      │
       │                               apps/dashboards/metrics
analytics.adapters                              │
       │                               frontend /dashboard
dashboard/reports/ai
frontend legacy (não wired)
```

**Regra:** novos módulos alimentam `CanonicalTaskRecord` via Integration Engine; legacy permanece intacto para compatibilidade.

---

## 5. Cobertura de testes

| Módulo | Testes | Prioridade |
|--------|--------|------------|
| `analytics/engine` | ✅ | CORE — manter |
| `analytics/services` | ✅ | CORE |
| `dashboard/services` | ✅ | CORE |
| `reports/engine` | ✅ | CORE |
| `ai/analyst` | ✅ | CORE |
| `apps/integrations` | ✅ 6 arquivos (~40 casos) | CORE — expandir |
| `apps/dashboards` | ✅ 6 casos | CORE |
| `apps/data_sources` | ✅ 5 casos | CORE |
| Legacy API views | ❌ | Adicionar Sprint 05 |
| Legacy Trello sync | ❌ | Adicionar Sprint 05 |
| Frontend E2E | ❌ | Sprint 05 |

---

## 6. Decisões de congelamento

1. **`dashboard/services/builders.py`** — não reescrever
2. **`core/migrations/0001_initial.py`** — Tenant orphan
3. **`integrations/trello/models.py`** — schema legacy estável
4. **Todas URLs API existentes** — compatibilidade retroativa
5. **`EntityHistory`, `Snapshot`** — FUTURE MVP
6. **Componentes frontend legacy** — preservados; não deletar
7. **Conceitos financeiros ENTERPRISE** — OUT OF SCOPE

---

*Documento v2.0 — engenharia reversa completa incluindo camada TIP `apps/` e Integration Engine.*
