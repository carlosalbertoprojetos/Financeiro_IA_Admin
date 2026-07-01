# Canonical Gap Analysis

Data: 2026-06-28

## Escopo

Auditoria das informacoes que ainda vinham exclusivamente do pipeline legado Trello (`integrations.trello`) e comparacao com o modelo canonico (`apps.integrations`).

Esta sprint nao remove o legado e nao cria novas engines analiticas.

## Resumo

Antes da consolidacao, o canonico representava principalmente:

- id;
- titulo;
- status/lista;
- board/projeto;
- prazo;
- labels basicas;
- alguns metadados.

O legado ainda era fonte exclusiva ou principal para actions, comentarios, historico, movimentacoes, membros completos, checklist operacional e varios campos derivados.

## Comentarios

### Fonte legado

- `integrations.trello.models.Action`
- `action_type="commentCard"`
- consumidores em `analytical_enrichment`, `communication_analysis`, `report_query`, `analytics`

### Gap canonico anterior

- `CanonicalTask` nao tinha campo de comentarios.
- `CanonicalTaskRecord.metadata` nao recebia comentarios.

### Consolidacao aplicada

- `CanonicalTask.comments`
- `metadata.comments`
- contagem em `derived_fields.comments_count`

### Dependencia remanescente

O cliente canonico Trello ainda nao busca actions por padrao; o mapper preenche comentarios quando `raw_payload["actions"]` estiver disponivel.

## Actions

### Fonte legado

- `integrations.trello.models.Action`
- usada para comments, movimentacoes, retrabalho, participantes, executor, timeline e comunicacao

### Gap canonico anterior

- Ausencia de lista de actions no objeto canonico.

### Consolidacao aplicada

- `CanonicalTask.actions`
- `CanonicalTask.history`
- `metadata.actions`
- `metadata.history`
- `derived_fields.actions_count`

### Dependencia remanescente

Ainda falta ampliar coleta canonica para trazer actions. Nenhum consumidor foi migrado nesta sprint.

## Membros

### Fonte legado

- `integrations.trello.models.Member`
- `Card.assignees`
- actions com `idMemberCreator`

### Gap canonico anterior

- O mapper canonico nao representava membros, responsaveis ou observadores.

### Consolidacao aplicada

- `CanonicalTask.members`
- `CanonicalTask.assignees`
- `CanonicalTask.watchers`
- `metadata.members`
- `metadata.assignees`
- `metadata.watchers`
- `derived_fields.members_count`
- `derived_fields.assignees_count`
- `derived_fields.watchers_count`

### Dependencia remanescente

O cliente canonico atual nao inclui `idMembers` em `CARD_FIELDS`; se o payload nao trouxer `idMembers`, o mapper mantem listas vazias sem inferir responsavel.

## Checklists

### Fonte legado

- `Card.raw_json.badges`
- `Card.raw_json.checklists` quando disponivel
- `apps.intelligence.services.checklist.intelligence`

### Gap canonico anterior

- Apenas badges parciais podiam existir no payload e nao havia campo canonico completo.

### Consolidacao aplicada

- `CanonicalTask.checklists`
- `metadata.checklists`
- `derived_fields.checklist_total`
- `derived_fields.checklist_completed`
- `derived_fields.checklist_completion_percent`

### Dependencia remanescente

Sem chamada dedicada a checklists completos, o mapper sintetiza itens a partir de badges quando necessario.

## Anexos

### Fonte legado

- Anexos nao eram modelados de forma rica no legado, mas podiam aparecer em `raw_json`.

### Gap canonico anterior

- Sem campo canonico.

### Consolidacao aplicada

- `CanonicalTask.attachments`
- `metadata.attachments`
- `derived_fields.attachments_count`
- evidencias de anexos em `CanonicalTask.evidence`

### Dependencia remanescente

O cliente canonico ainda nao busca attachments explicitamente.

## Labels

### Fonte legado

- `Card.labels`

### Gap canonico anterior

- Labels ja eram preservadas em `metadata.labels`, mas nao como campo de primeira classe do objeto canonico.

### Consolidacao aplicada

- `CanonicalTask.labels`
- `metadata.labels`
- `derived_fields.labels_count`

## Historico

### Fonte legado

- `Action`
- `CardStatusHistory`
- `EntityHistory`
- `TimelineEvent`

### Gap canonico anterior

- Sem campo `history`.

### Consolidacao aplicada

- `CanonicalTask.history`
- `metadata.history`

### Dependencia remanescente

Historico derivado de `CardStatusHistory`, `EntityHistory` e `TimelineEvent` ainda nao foi migrado para consumidores canonicos. O mapper representa actions brutas quando disponiveis.

## Movimentacoes

### Fonte legado

- `Action.updateCard` com `listBefore` e `listAfter`
- `CardStatusHistory`

### Gap canonico anterior

- Sem campo de movimentacoes.

### Consolidacao aplicada

- `CanonicalTask.movements`
- `metadata.movements`
- `derived_fields.movements_count`

### Dependencia remanescente

Movimentacoes dependem de actions no payload canonico.

## Campos derivados

### Fonte legado

- analytics/adapters e analytics/engine
- report_query/analytical_enrichment
- checklist intelligence
- risk/communication engines

### Gap canonico anterior

- Campos derivados ficavam espalhados em consumidores e metadados avulsos.

### Consolidacao aplicada

- `CanonicalTask.derived_fields`
- `metadata.derived_fields`

Campos consolidados:

- checklist total/concluido/percentual;
- comentarios;
- anexos;
- actions;
- movimentacoes;
- labels;
- membros;
- responsaveis;
- observadores;
- riscos documentados;
- evidencias documentadas;
- completude documental;
- flags `closed` e `due_complete`.

## Conclusao

O modelo canonico agora consegue representar integralmente um card Trello quando o payload traz os dados. A lacuna remanescente principal nao e de modelo, mas de coleta e migracao de consumidores.

