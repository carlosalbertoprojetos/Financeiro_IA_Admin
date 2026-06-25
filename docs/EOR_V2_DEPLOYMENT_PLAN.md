# EOR V2 — Plano de Implantação

**Versão:** 2.0  
**Data:** 2026-06-20

## Pré-requisitos

- PostgreSQL configurado
- Redis (opcional, para Celery)
- Trello API Key + Token
- OpenAI API Key (opcional, para resumos com IA)

## Etapas de Implantação

### Fase 1 — Backend (Dia 1)

1. Deploy código com `apps.intelligence` em `INSTALLED_APPS`
2. Executar migrações:
   ```bash
   python manage.py migrate tip_intelligence
   ```
3. Validar health check: `GET /health/`
4. Validar módulo: `GET /api/v1/intelligence/`

### Fase 2 — Sync + Timeline (Dia 1-2)

1. Executar sync legacy de boards existentes:
   ```bash
   python manage.py sync_trello_board <BOARD_ID>
   ```
2. Timeline events são gerados automaticamente pós-sync
3. Validar: `GET /api/v1/intelligence/timeline/?board_id=<BOARD_ID>`

### Fase 3 — Pipeline de Inteligência (Dia 2)

1. Executar pipeline completo:
   ```bash
   curl -X POST http://localhost:8000/api/v1/intelligence/pipeline/ \
     -H "Content-Type: application/json" \
     -d '{"board_id": "<BOARD_ID>", "use_ai": false}'
   ```
2. Validar score: `GET /api/v1/intelligence/score/?board_id=<BOARD_ID>`
3. Validar relatório: `GET /api/v1/intelligence/report/?board_id=<BOARD_ID>`

### Fase 4 — Integração Frontend (Dia 3-5)

1. Consumir `/api/v1/intelligence/dashboard/?level=management`
2. Adicionar rota AI Insights no frontend
3. Conectar relatório V2 ao fluxo de download PDF

### Fase 5 — Produção (Dia 5-7)

1. Configurar Celery Beat para sync periódico (V3)
2. Habilitar OpenAI via Settings UI
3. Monitorar logs de pipeline

## Checklist de Validação

- [ ] Migrações aplicadas sem erro
- [ ] Sync Trello popula timeline_events
- [ ] KPIs retornam dados para board sincronizado
- [ ] Operational Score calculado (0-100)
- [ ] Relatório executivo com 14 seções
- [ ] Testes passando: `python manage.py test apps.intelligence`

## Variáveis de Ambiente

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `DATABASE_URL` / PG vars | Sim | PostgreSQL |
| `TRELLO_API_KEY` | Sim | Trello API |
| `TRELLO_API_TOKEN` | Sim | Trello token |
| `OPENAI_API_KEY` | Não | IA executiva |
| `CELERY_BROKER_URL` | Não | Async processing |

## Monitoramento

- Log: `apps.intelligence.services.orchestrator` — pipeline completion
- Log: `apps.intelligence.services.timeline.engine` — event count
- Admin: `/admin/` — TimelineEvent, CardEnrichment, KnowledgeBaseEntry, OperationalScoreSnapshot
