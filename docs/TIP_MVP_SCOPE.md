# TIP MVP SCOPE — Trello Intelligence Platform

**Versão:** 2.0  
**Data:** 2026-06-19  
**Produto:** TIP (Trello Intelligence Platform)  
**MVP inicial:** Trello + Excel

---

## VISÃO DO PRODUTO

TIP é uma plataforma de **inteligência operacional** que transforma dados de ferramentas de trabalho (inicialmente Trello e Excel) em **dashboards**, **relatórios**, **gráficos** e **análises automáticas** exportáveis em PDF — acessível a gestores e equipes sem conhecimento técnico.

A arquitetura é preparada para múltiplas fontes (CSV, Jira, ClickUp, Monday), mas o MVP comercial entrega valor imediato com **Trello** e **Excel**.

**Posicionamento:** ferramenta de produtividade e fluxo Kanban — **não** plataforma financeira (CFO, Forecast, ROI).

---

## PROBLEMA

| Dor | Impacto |
|-----|---------|
| Falta de visibilidade sobre lead time, gargalos e atrasos | Decisões reativas |
| Dados dispersos entre Trello e Excel | Visão fragmentada |
| Relatórios manuais demorados | Perda de tempo gerencial |
| Configuração técnica de APIs | Barreira para usuários finais |
| Ausência de síntese executiva | Dificuldade de comunicar status à liderança |

---

## PÚBLICO-ALVO

### Primário (MVP)

| Persona | Necessidade |
|---------|-------------|
| **Gestor operacional** | Dashboard, gargalos, PDF para reuniões |
| **Scrum Master / PM** | Throughput, aging, filtros |
| **Analista de processos** | Relatórios, gaps, export |

### Secundário (pós-MVP)

- Diretor de operações (multi-board)
- Consultor externo (Excel de clientes sem Trello)

### Fora do público MVP

- CFO / Controller
- Investidores (ROI, Business Value)

---

## JORNADA DO USUÁRIO

```
Login → Integrações → Conectar Trello → Sync → Dashboard → (Filtros) → Análise → PDF
                              ↓
                        Import Excel (Sprint 03)
```

### Etapas e status atual

| # | Etapa | Status atual |
|---|-------|--------------|
| 1 | Login demo | ✅ `/login` + localStorage |
| 2 | Conectar Trello (Key, Token) | ✅ `/integrations` modal |
| 3 | Testar conexão | ✅ botão "Testar conexão" |
| 4 | Sync | ✅ "Sync Now" → `POST .../trello/sync/` |
| 5 | Dashboard canônico | ✅ `/dashboard` — KPIs + 4 gráficos |
| 6 | Filtros avançados | ❌ Sprint 02 |
| 7 | Import Excel | ❌ Sprint 03 |
| 8 | Análise automática | ❌ Sprint 04 (backend ✅) |
| 9 | Export PDF | ❌ Sprint 04 (backend ✅) |

---

## FUNCIONALIDADES

### CORE MVP

| ID | Funcionalidade | Backend | Frontend | Notas |
|----|----------------|---------|----------|-------|
| F01 | Config Trello (Key, Token) | ✅ data-sources + integrations | ✅ modal | Credenciais criptografadas |
| F02 | Teste conexão | ✅ connect endpoint | ✅ | |
| F03 | Sync Trello | ✅ SyncEngine + legacy | ✅ | Dois caminhos coexistem |
| F04 | Import Excel | ❌ placeholder 501 | ❌ | Sprint 03 |
| F05 | Normalização canônica | ✅ CanonicalTask | — | Integration Engine |
| F06 | Dashboard KPIs | ✅ `/dashboards/metrics/` | ✅ | Tasks canônicas |
| F07 | Gráficos operacionais | ✅ canonical metrics | ✅ | status, provider, trend, overdue |
| F08 | Filtro colaborador | ⚠️ legacy only | ❌ | Sprint 02 |
| F09 | Filtro equipe | ⚠️ API team legacy | ❌ | Sprint 02 |
| F10 | Filtro período | ⚠️ trend 7d | ⚠️ | Expandir Sprint 02 |
| F11 | Filtro lista/coluna | ⚠️ status field | ❌ | Sprint 02 |
| F12 | Filtro etiqueta | ⚠️ metadata labels | ❌ | Sprint 02 |
| F13 | Filtro urgência | ❌ | ❌ | Sprint 02 |
| F14 | Relatório gargalos | ✅ legacy API | ❌ UI | Sprint 04 |
| F15 | Análise automática | ✅ AI API | ❌ UI | Sprint 04 |
| F16 | Export PDF | ✅ reports API | ❌ UI | Sprint 04 |
| F17 | Multi-provider UI | ⚠️ Trello ativo | ⚠️ Jira/ClickUp placeholder | |

### FUTURE MVP

Comparativos, benchmarking, alertas, Celery async, CSV, Jira/ClickUp/Monday completos, auth produção, unificação dual data plane.

### ENTERPRISE (fora do TIP)

Forecast, Recovery, Business Value, ROI, CFO Virtual, RBAC multi-tenant.

---

## TELAS

| Rota | Tela | Prioridade | Status |
|------|------|------------|--------|
| `/login` | Autenticação demo | P0 | ✅ |
| `/dashboard` | Dashboard operacional v1 | P0 | ✅ |
| `/integrations` | Conectores (Trello ativo) | P0 | ✅ |
| `/analytics` | Análises avançadas | P1 | ⚠️ placeholder |
| `/reports` | Relatórios + PDF | P1 | ⚠️ placeholder |
| `/settings` | Configurações | P2 | ⚠️ placeholder |
| `/import` | Import Excel | P0 | ❌ Sprint 03 |

**Shell:** AppShell + sidebar + PermissionGuard + navegação por permissões.

---

## INTEGRAÇÕES

### MVP

| Fonte | Backend | Frontend | Engine |
|-------|---------|----------|--------|
| **Trello** | ✅ dual path | ✅ | SyncEngine + IngestionEngine |
| **Excel** | ❌ | ❌ | Adapter planejado |
| **PostgreSQL** | ✅ | — | ORM + CanonicalTaskRecord |
| **OpenAI** | ✅ analyze | ❌ UI | Sprint 04 |

### Arquitetura multi-fonte (implementada)

```
apps/integrations/
├── core/          → SyncEngine, IngestionEngine, Registry, Queue, StateStore
├── trello/        → TrelloAdapter (✅)
├── adapters/      → jira, clickup (stub)
└── workers/       → trello_worker (✅)

        ↓
CanonicalTaskRecord
        ↓
apps/dashboards/metrics
        ↓
frontend /dashboard
```

### Caminho legacy (preservado)

```
integrations/trello/ → analytics/ → dashboard/ → reports/ + ai/
```

---

## RELATÓRIOS

| Relatório | API | UI | Sprint |
|-----------|-----|-----|--------|
| Dashboard canônico | `GET /api/v1/dashboards/metrics/` | ✅ | — |
| Dashboard legacy (KPIs Kanban) | `/api/dashboard/*` | ❌ (legacy components) | 02 |
| Gargalos | `/api/dashboard/bottlenecks/` | ❌ | 04 |
| Equipe | `/api/analytics/metrics/team/` | ❌ | 04 |
| Gaps | `/api/analytics/metrics/gaps/` | ❌ | 04 |
| PDF executivo | `POST /api/v1/reports/executive/` | ❌ | 04 |

### Métricas canônicas (dashboard v1)

| Métrica | Onde |
|---------|------|
| Tasks por status | Bar chart |
| Tasks atrasadas | KPI + tabela |
| Distribuição por provider | Pie chart |
| Tendência 7 dias | Line chart |

### Métricas legacy (Kanban, via API existente)

Lead time, cycle time, throughput, aging, delay rate, rework rate, health score, WIP.

---

## EXPORTAÇÕES

| Formato | Backend | UI | Sprint |
|---------|---------|-----|--------|
| PDF executivo | ✅ | ❌ | 04 |
| JSON (APIs) | ✅ | — | — |
| Excel/CSV export | ❌ | ❌ | FUTURE |

---

## ROADMAP

### Fase 0 — Recuperação documental ✅

- Classificação v2.0
- Escopo MVP v2.0
- Plano implementação v2.0

### Fase 1 — MVP Comercial (Sprints 01–05)

| Marco | Entrega | Progresso |
|-------|---------|-----------|
| M1 | Trello conectável pela UI | **~80%** — falta polish e docs |
| M2 | Dashboard + filtros | **~40%** — dashboard v1 ok, filtros pendentes |
| M3 | Excel import | **0%** |
| M4 | PDF + Análise UI | **~30%** — backend ok |
| M5 | Hardening + demo | **~20%** — testes parciais |

### Fase 2 — FUTURE MVP

Comparativos, alertas, CSV, Jira/ClickUp/Monday, Celery, multi-board, auth produção.

### Fase 3 — ENTERPRISE

Módulos financeiros, RBAC multi-tenant.

---

## Critérios de aceite MVP TIP

- [x] Usuário configura Trello pela interface (Key, Token)
- [x] Usuário testa conexão
- [x] Usuário sincroniza com um clique
- [ ] Usuário importa Excel e vê dados no dashboard
- [x] Dashboard exibe métricas reais (canônicas)
- [ ] Filtros: colaborador, equipe, período, lista, etiqueta, urgência
- [ ] Usuário gera análise automática na UI
- [ ] Usuário exporta PDF executivo
- [x] Nenhuma API existente quebrada
- [x] Nenhum módulo removido ou reescrito

---

## Fora do escopo TIP

CFO Virtual, Forecast, Recovery, Business Value, ROI, Executive Board financeiro, RBAC enterprise, Pilot Readiness.

---

*Escopo v2.0 — reflete estado atual pós Integration Engine e frontend shell.*
