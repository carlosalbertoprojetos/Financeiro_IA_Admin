# Canonical Consumers

Data: 2026-06-28

## Escopo

Mapa dos consumidores de dados operacionais Trello e plano de migracao gradual para o modelo canonico consolidado.

Nenhuma migracao de consumidor foi executada nesta sprint.

## Consumidores ja canonicos

| Consumidor | Fonte atual | Status |
| --- | --- | --- |
| `apps.dashboards.services.canonical_metrics` | `CanonicalTaskRecord` | Canonico |
| `apps.dashboards.services.canonical_analytics` | `CanonicalTaskRecord` via dashboard canonico | Canonico |
| `apps.dashboards.services.canonical_report` | `CanonicalTaskRecord` via dashboard canonico | Canonico |
| `apps.reports.views.CanonicalExecutiveReportView` | metrics canonicas | Canonico |
| `apps.integrations.workers.trello_worker` | eventos canonicos + `CanonicalTaskRecord` | Canonico |
| `apps.integrations.services.analytics_sync` | `CanonicalTaskRecord` | Canonico |
| `apps.dashboards.services.scope` | `CanonicalTaskRecord`, `IntegrationConnection` | Canonico |
| `apps.integrations.trello.connections` | `CanonicalTaskRecord`, `IntegrationConnection` | Canonico para status |

## Consumidores ainda legados

| Consumidor | Fonte legada | Motivo |
| --- | --- | --- |
| `analytics.adapters` | `integrations.trello.models.Card`, `Action`, `CardStatusHistory` | Gera `CardRecord` e `ActionRecord` para metricas ricas |
| `analytics.engine.metrics` | `CardRecord`, `ActionRecord` derivados do legado | Lead/cycle/throughput/aging/rework |
| `analytics.services.builders` | records derivados do legado | Overview, team, cards, gaps |
| `apps.intelligence.services.report_query.templates.registry` | `Card`, `Action` | Templates segmentados ainda carregam ORM legado |
| `apps.intelligence.services.report_query.engine.queryset_builder` | `Card` | Filtros trabalham sobre ORM legado |
| `apps.intelligence.services.report_query.engine.post_processor` | `Card` | Linhas de card ainda partem do legado |
| `apps.intelligence.services.report_query.engine.analytical_enrichment` | `Card`, `Action` | Comunicacao, workload, qualidade e riscos por card |
| `apps.intelligence.services.report_query.engine.card_metrics` | `Card`, `Action` | Filtros de status, membro, checklist, risco |
| `apps.intelligence.providers.trello` | `Board`, `Card`, `Action` | Provider de inteligencia le diretamente legado |
| `apps.intelligence.services.checklist.intelligence` | `Card.raw_json` | Checklist a partir do legado |
| `apps.intelligence.services.risk_engine.scorer` | `Card`, timeline, checklist, comunicacao | Risk engine le legado e timeline |
| `apps.intelligence.services.bottleneck_detector.detector` | `Action`, `Card` | Gargalos e comentarios |
| `apps.intelligence.services.enrichment.engine` | `Card`, `Action` | Enriquecimento textual e comments |
| `apps.intelligence.services.timeline.engine` | `Action`, `Card` | Timeline a partir de actions legadas |
| `apps.intelligence.services.communication_analysis.analyzer` | `Card`, comments/actions | Comunicacao operacional |
| `apps.intelligence.services.operational_score.scorer` | KPI/risk/bottleneck legados | Score operacional |
| `apps.intelligence.services.kpi.engine` | legado | KPIs do board |
| `apps.intelligence.services.product_readiness.usage` | legado + canonico | Auditoria de uso cruza fontes |

## Consumidores fora do escopo desta sprint

Nao foram alterados:

- DAL;
- OLE;
- Discovery;
- Executive Story;
- Report Engine;
- Risk Engine;
- Timeline;
- Report Query;
- Analytics engine.

## Plano de migracao gradual

### Fase 1 - Bridge canonico para records analiticos

Criar adaptadores puros:

- `CanonicalTaskRecord -> CardRecord`
- `metadata.actions -> ActionRecord`

Impacto: permite reutilizar `analytics.engine.metrics` sem ORM legado.

Risco: divergencia metodologica em datas de conclusao e historico.

Rollback: manter `analytics.adapters.load_board_records` como fonte padrao.

### Fase 2 - Queryset canonico para Report Query

Criar camada de leitura canonica equivalente aos filtros de `queryset_builder`.

Impacto: Report Query passa a operar sobre `CanonicalTaskRecord`.

Risco: filtros por membro, checklist e status especial precisam de equivalencia exata.

Rollback: feature flag para retornar ao `Card` legado.

### Fase 3 - Timeline e comunicacao a partir de `metadata.actions`

Ler `metadata.actions`, `metadata.comments` e `metadata.movements`.

Impacto: reduz dependencia direta de `Action`.

Risco: payload canonico precisa garantir actions completas.

Rollback: manter `Action` como fonte de timeline ate cobertura real.

### Fase 4 - Risk, bottleneck e operational score

Migrar consumidores para records canonicos e campos derivados.

Impacto: Risk/score deixam de depender de ORM Trello.

Risco: score muda se algum dado de timeline/checklist estiver ausente.

Rollback: comparacao lado a lado por board antes de trocar fonte padrao.

### Fase 5 - Desativacao controlada da leitura legada

Somente apos equivalencia em board real:

- relatorios;
- dashboards;
- risk;
- timeline;
- score.

Impacto: legado deixa de ser fonte de inteligencia.

Risco: perda silenciosa de dados se conectores canonicos estiverem incompletos.

Rollback: manter sync legado e consumers antigos por uma release.

## Criterios de migracao

Cada consumidor so deve migrar quando:

1. o payload canonico tiver os campos necessarios;
2. houver teste de equivalencia com card realista;
3. houver diferencas documentadas;
4. houver feature flag ou caminho de rollback;
5. nenhum motor analitico precisar conhecer estrutura especifica do Trello.

