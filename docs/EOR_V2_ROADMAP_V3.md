# EOR V3 — Roadmap

**Horizonte:** Pós-V2 (Q3-Q4 2026)

## Objetivo V3

Consolidar arquitetura dual em plataforma unificada, com UI executiva completa, auth real e integrações multi-provider.

---

## Q3 2026 — Consolidação

### Unificação de Dados
- [ ] Bridge `CanonicalTaskRecord` → `CardRecord` para analytics unificado
- [ ] Enriquecer platform sync para capturar actions/events
- [ ] Deprecar APIs `/api/*` legacy com redirect para `/api/v1/*`

### Autenticação & Multi-tenant
- [ ] JWT/session auth real
- [ ] Enforce RBAC em todas as views
- [ ] Auth headers no frontend
- [ ] Workspace isolation por tenant

### Frontend Executivo
- [ ] Feature `ai-insights` com rota e UI
- [ ] Dashboard executivo (operational/management/director/ceo)
- [ ] Analytics com charts (trend_7d, overdue)
- [ ] Preview de relatório in-app
- [ ] Reconectar métricas legacy ou migrar para intelligence API

### Automação
- [ ] Celery Beat: sync periódico
- [ ] Pipeline intelligence pós-sync via `sync_completed` signal
- [ ] Wire `IngestionEngine` para incremental updates

---

## Q4 2026 — Expansão

### Multi-provider
- [ ] Jira adapter (WorkManagementProvider)
- [ ] ClickUp adapter
- [ ] Asana adapter (research)
- [ ] Cross-provider aggregation dashboard

### IA Avançada
- [ ] Wire OpenAI config from `WorkspaceConfig`
- [ ] Persistir diagnósticos IA
- [ ] Fine-tuned prompts por indústria
- [ ] Alertas proativos (email/Slack)

### Relatórios & Export
- [ ] PDF V2 com 14 seções (ReportLab extension)
- [ ] Export CSV/Excel
- [ ] Report scheduling
- [ ] Histórico de geração

### Observabilidade
- [ ] Métricas de pipeline (Prometheus)
- [ ] Audit log de credenciais
- [ ] Data quality dashboard

---

## V3+ — Visão

- Real-time event streaming (Kafka)
- ML models para predição (substituir heurísticas)
- Benchmarking cross-organização
- Mobile app executivo
- Integração BI (Power BI, Looker)

---

## Priorização

| Prioridade | Item | Impacto |
|------------|------|---------|
| P0 | Auth real | Segurança |
| P0 | Frontend executive dashboard | Adoção |
| P1 | Unified data path | Qualidade analytics |
| P1 | Celery Beat sync | Automação |
| P2 | Jira/ClickUp | Expansão mercado |
| P2 | PDF V2 | Entrega executiva |
| P3 | ML predição | Diferenciação |
