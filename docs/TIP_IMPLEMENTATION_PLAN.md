# TIP IMPLEMENTATION PLAN — Recuperação Controlada

**Versão:** 2.0  
**Data:** 2026-06-19  
**Restrições:** não apagar, não reescrever, não remover código, manter compatibilidade de APIs.

---

## Princípios de execução

| Princípio | Aplicação |
|-----------|-----------|
| **Additive only** | Novos arquivos/rotas; APIs existentes intactas |
| **Adapter pattern** | Excel/Jira → `CanonicalTask` via Integration Engine |
| **Dual data plane** | Legacy ORM + CanonicalTaskRecord coexistem |
| **UI wraps backend** | Consumir APIs antes de criar novas |
| **No rewrite** | Builders legacy congelados |

---

## Progresso atual (baseline 2026-06-19)

| Área | Concluído | Pendente |
|------|-----------|----------|
| Integration Engine | SyncEngine, IngestionEngine, Registry, Queue, StateStore | Excel adapter |
| Trello adapter | fetch, fetch_incremental, connect/sync/status APIs | UI board picker |
| Frontend shell | login, dashboard v1, integrations Trello | analytics, reports, settings |
| Canonical dashboard | API + UI + testes | Filtros avançados |
| Legacy stack | Intacto | UI legacy não wired |
| Excel | Placeholder API | Módulo completo |
| PDF + AI UI | Backend ok | Frontend Sprint 04 |
| Testes | ~50 casos apps/integrations + dashboards | API views, E2E |

**Sprint 01 estimada ~70% concluída** (entregas core feitas; falta polish, docs demo, auth token nos requests).

---

## Visão das sprints

```
Sprint 01 ──► Trello Setup & Sync        [~70% ✅]
     │
Sprint 02 ──► Dashboard comercial + Filtros
     │
Sprint 03 ──► Excel Import
     │
Sprint 04 ──► Relatórios + PDF + Análise UI
     │
Sprint 05 ──► Hardening + Demo readiness
```

---

## Sprint 01 — Trello Setup & Sync Integration

**Objetivo:** Usuário configura e sincroniza Trello pela interface.

### Entregas

| # | Entrega | Status |
|---|---------|--------|
| 1.1 | UI conectar Trello (Key, Token) | ✅ `/integrations` |
| 1.2 | Teste conexão | ✅ modal → connect API |
| 1.3 | Credenciais criptografadas | ✅ Fernet + IntegrationConnection |
| 1.4 | Sync via UI | ✅ SyncEngine |
| 1.5 | Status polling | ✅ 10s |
| 1.6 | Integration Engine | ✅ (extra — além do plano v1) |
| 1.7 | Auth token em API calls | ❌ pendente |
| 1.8 | Board picker / workspace | ⚠️ API existe, UI não |
| 1.9 | Documentação demo | ❌ |

### Restante Sprint 01 (~3–5 dias)

1. Propagar auth token nos fetch do frontend
2. Board ID picker (consumir `/connections/<id>/boards/`)
3. `docs/DEMO_GUIDE.md` — fluxo login → connect → sync → dashboard
4. Empty state polish pós-sync

### O que NÃO alterar

- `TrelloClient` legacy
- `sync_board()` legacy
- URLs API existentes

### Riscos

| Risco | Mitigação |
|-------|-----------|
| Dual sync confunde operação | Documentar caminhos; convergir leitura em CanonicalTask |
| Credenciais | ✅ criptografia implementada |

### Critério de done

- [x] Setup → test → sync → dashboard com dados
- [ ] Demo repetível documentada
- [ ] Token auth nos requests API

---

## Sprint 02 — Dashboard Comercial & Filtros

**Objetivo:** Dashboard completo com filtros e resiliência.

### Entregas

| # | Entrega | Tipo |
|---|---------|------|
| 2.1 | Filtros: status, provider, project_id | Frontend (parcial ✅) |
| 2.2 | Filtros: colaborador, equipe, lista, etiqueta, urgência | Frontend |
| 2.3 | Consumir legacy APIs para KPIs Kanban (opcional) ou enriquecer canônico | Backend additive |
| 2.4 | Loading parcial por seção | Frontend |
| 2.5 | Empty states refinados | Frontend |
| 2.6 | Query params filtros (backward compatible) | Backend additive |
| 2.7 | Unificar ou documentar dual dashboard | Docs |

### Esforço: **8–10 dias** (reduzido — dashboard v1 já existe)

### Dependências: Sprint 01 restante

### Ordem

1. Expandir filtros FilterBar (novo componente canônico, não reescrever legacy)
2. Filtros server-side opcionais em `/dashboards/metrics/`
3. Loading parcial + error boundaries
4. Testes filtros

### Critério de done

- 6 filtros funcionais
- Dashboard resiliente a falha parcial

---

## Sprint 03 — Excel Import

**Objetivo:** Segunda fonte MVP via Integration Engine.

### Entregas

| # | Entrega | Tipo |
|---|---------|------|
| 3.1 | `integrations/excel/` ou `apps/integrations/excel/` | Backend novo |
| 3.2 | Parser `.xlsx` | Backend |
| 3.3 | ExcelAdapter → CanonicalTask | Integration Engine |
| 3.4 | `POST /api/v1/data-sources/excel/import/` | Backend |
| 3.5 | Tela `/import` | Frontend |
| 3.6 | Template Excel documentado | Docs |

### Esforço: **12–16 dias**

### Dependências: Sprint 01 estável

### O que NÃO alterar

- `analytics/engine/metrics.py`
- Legacy models (Excel escreve em CanonicalTaskRecord)

### Riscos

| Risco | Mitigação |
|-------|-----------|
| Planilhas heterogêneas | Wizard mapeamento + template |

### Critério de done

- Upload Excel → dashboard canônico atualizado
- Trello continua independente

---

## Sprint 04 — Relatórios, PDF & Análise UI

**Objetivo:** Expor backend reports/AI na interface.

### Entregas

| # | Entrega | Tipo |
|---|---------|------|
| 4.1 | `/reports` funcional (gaps, team, bottlenecks) | Frontend |
| 4.2 | Botão Export PDF | Frontend |
| 4.3 | Download PDF blob | Frontend |
| 4.4 | Modal/página análise AI | Frontend |
| 4.5 | Fallback determinístico | Backend novo `ai/deterministic.py` |

### Esforço: **8–12 dias** (UI only — backend ✅)

### Dependências: Sprint 02 (filtros)

### O que NÃO alterar

- `ExecutiveReportView`, `analyze_metrics()`, `pdf_builder`

### Critério de done

- PDF baixável
- Análise visível (AI ou determinística)
- Reports page funcional

---

## Sprint 05 — Hardening, Testes & Demo Readiness

**Objetivo:** MVP demonstrável comercialmente.

### Entregas

| # | Entrega |
|---|---------|
| 5.1 | Testes API views legacy |
| 5.2 | Testes sync Trello (mock) |
| 5.3 | Testes Excel import |
| 5.4 | E2E Playwright (login → sync → dashboard → PDF) |
| 5.5 | README + DEMO_GUIDE atualizados |
| 5.6 | Error handling padronizado frontend |
| 5.7 | CI pipeline básico |

### Esforço: **8–10 dias**

### Critério de done

- ≥80% fluxos MVP testados
- Demo < 10 minutos
- Zero breaking changes

---

## Resumo consolidado

| Sprint | Foco | Esforço restante | Progresso |
|--------|------|------------------|-----------|
| **01** | Trello Setup & Sync | 3–5 dias | ~70% |
| **02** | Dashboard & Filtros | 8–10 dias | ~30% |
| **03** | Excel Import | 12–16 dias | 0% |
| **04** | Reports + PDF + AI | 8–12 dias | ~30% backend |
| **05** | Hardening & Demo | 8–10 dias | ~20% |
| **Total restante** | | **~39–53 dias** (~8–11 semanas) | |

---

## Diagrama de dependências

```
Sprint 01 (restante)
       │
       ├──────────────┐
       ▼              ▼
 Sprint 02        Sprint 03
 Dashboard        Excel
       │              │
       └──────┬───────┘
              ▼
        Sprint 04
        Reports/PDF/AI
              │
              ▼
        Sprint 05
        Hardening
```

Sprint 03 pode iniciar em paralelo com Sprint 02 após conclusão Sprint 01.

---

## Artefatos já criados (additive — preservar)

### Backend

```
apps/integrations/          ← Integration Engine completo
apps/data_sources/          ← Trello connect/sync/status
apps/dashboards/            ← Canonical metrics
apps/users, settings, exports, analytics, reports, ai_insights  ← facades
integrations/trello/        ← legacy intacto
```

### Frontend

```
src/features/dashboards/    ← Dashboard v1 funcional
src/features/integrations/  ← Trello funcional
src/features/analytics|reports|settings/  ← placeholders
src/layouts/, src/shared/   ← shell auth/nav
components/                 ← legacy congelado
```

---

## Congelado em todas as sprints

| Item | Motivo |
|------|--------|
| `dashboard/services/builders.py` | Compatibilidade |
| `core/migrations/0001_initial.py` | Tenant enterprise |
| URLs API legacy | Backward compatibility |
| `integrations/trello/models.py` | ORM legacy |
| Frontend legacy components | Migração gradual |
| ENTERPRISE concepts | OUT OF SCOPE |

---

## Métricas de progresso

| Marco | % MVP | Status |
|-------|-------|--------|
| Trello conectável UI | 25% | ✅ |
| Integration Engine | 30% | ✅ |
| Dashboard canônico | 45% | ✅ |
| Filtros completos | 55% | ❌ |
| Excel import | 70% | ❌ |
| PDF + Análise UI | 90% | ❌ |
| Demo comercial | 100% | ❌ |

**Progresso estimado global: ~45%**

---

## Próximo passo imediato

1. **Fechar Sprint 01:** auth token nos requests + DEMO_GUIDE
2. **Iniciar Sprint 02:** filtros avançados no dashboard canônico
3. **Preparar Sprint 03:** `docs/EXCEL_TEMPLATE.md` (schema colunas)

**Nenhuma alteração destrutiva. Apenas additive a partir daqui.**

---

*Plano v2.0 — reflete Integration Engine, frontend shell e progresso real da base.*
