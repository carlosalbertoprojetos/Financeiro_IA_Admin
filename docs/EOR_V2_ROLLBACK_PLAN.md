# EOR V2 — Plano de Rollback

**Versão:** 2.0  
**Data:** 2026-06-20

## Cenários de Rollback

### Rollback Completo (remover V2)

1. Reverter deploy para commit anterior à V2
2. Remover `apps.intelligence` de `INSTALLED_APPS` em `tip_backend/settings/base.py`
3. Remover rota em `apps/urls.py`
4. Reverter hook em `integrations/trello/services/sync.py` (bloco timeline)
5. Opcional: reverter migração:
   ```bash
   python manage.py migrate tip_intelligence zero
   ```

### Rollback Parcial (desabilitar pipeline, manter dados)

1. Remover apenas rota `/api/v1/intelligence/pipeline/`
2. Comentar hook pós-sync em `sync.py`
3. Dados em `timeline_events` permanecem para análise futura

### Rollback de Migração

```bash
python manage.py migrate tip_intelligence 0001_initial --fake
python manage.py migrate tip_intelligence zero
```

**Atenção:** Rollback de migração apaga `timeline_events`, `card_enrichment`, `knowledge_base_entry`, `operational_score_snapshot`.

## Impacto por Componente

| Componente | Rollback impact | Legacy fallback |
|------------|-----------------|-----------------|
| Timeline Engine | Sem timeline V2 | Action ORM ainda disponível |
| KPI Engine | Perde KPIs estendidos | `/api/analytics/metrics/` |
| Executive Report V2 | Perde relatório 14 seções | `/api/v1/reports/executive/` |
| Operational Score | Perde score proprietário | Dashboard health score legacy |
| WorkManagementProvider | Sem impacto | Trello sync inalterado |

## Procedimento de Emergência

1. **Detectar falha:** Pipeline retorna 500 ou sync falha pós-hook timeline
2. **Mitigação imediata:** Comentar try/except block em `sync.py` (hook timeline)
3. **Validar:** Sync Trello funciona sem timeline
4. **Investigar:** Logs em `apps.intelligence.services.timeline.engine`
5. **Corrigir ou rollback:** Deploy fix ou revert completo

## Preservação de Dados

Antes de rollback destrutivo:

```bash
python manage.py dumpdata tip_intelligence --indent 2 > intelligence_backup.json
```

## Tempo Estimado de Rollback

| Tipo | Tempo |
|------|-------|
| Desabilitar hook sync | 5 min |
| Revert deploy | 15 min |
| Rollback migração + deploy | 30 min |

## Comunicação

- Notificar equipe sobre fallback para APIs legacy
- Documentar incidente e causa raiz
- Planejar re-deploy após correção
