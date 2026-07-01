# Canonical Consolidation Report

Data: 2026-06-28

## Objetivo

Consolidar o modelo canonico de inteligencia do EOR para que ele consiga representar integralmente um card Trello sem perda de informacao relevante para motores analiticos.

Esta sprint nao remove o legado, nao cria engines novas e nao altera DAL, OLE, Discovery, Executive Story ou Report Engine.

## Alteracoes realizadas

### Modelo canonico

`apps.integrations.core.canonical.CanonicalTask` foi expandido com campos opcionais:

- `description`;
- `structured_description`;
- `comments`;
- `actions`;
- `history`;
- `movements`;
- `checklists`;
- `attachments`;
- `members`;
- `assignees`;
- `watchers`;
- `labels`;
- `dates`;
- `derived_fields`;
- `evidence`;
- `raw`.

A compatibilidade foi preservada:

- campos antigos continuam existindo;
- `metadata` continua sendo o ponto de persistencia em `CanonicalTaskRecord`;
- `as_dict()` continua retornando `source_provider`, `source_id`, `title`, `status`, `due_date`, `project_id` e `metadata`.

### Mapper Trello

`apps.integrations.trello.mapper` passou a preencher o modelo canonico consolidado quando o payload possui:

- card;
- listas;
- membros;
- actions;
- comentarios;
- movimentacoes;
- checklists;
- anexos;
- labels;
- datas;
- descricao estruturada;
- evidencias;
- campos derivados.

O mapper segue tolerante: se o payload atual nao trouxer actions, membros ou attachments, os campos ficam vazios e nenhum dado e inventado.

### Persistencia canonica

`CanonicalTask.metadata_with_canonical_fields()` centraliza o espelhamento dos campos ricos em `metadata`.

Atualizados:

- `apps.integrations.core.engine`;
- `apps.integrations.core.ingestion_engine`;
- `apps.integrations.services.task_persistence`.

## Cobertura do modelo canonico

| Categoria | Cobertura de modelo | Preenchimento pelo mapper Trello |
| --- | --- | --- |
| Descricao estruturada | Coberto | Sim |
| Comentarios | Coberto | Sim, se `actions` vierem no payload |
| Actions | Coberto | Sim, se `actions` vierem no payload |
| Historico | Coberto | Sim, como actions normalizadas |
| Movimentacoes | Coberto | Sim, a partir de `listBefore/listAfter` |
| Checklist completo | Coberto | Sim, se `checklists` vierem; fallback por badges |
| Anexos | Coberto | Sim, se `attachments` vierem |
| Membros | Coberto | Sim, se `members` e ids vierem |
| Responsaveis | Coberto | Sim, a partir de `idMembers` |
| Observadores | Coberto | Sim, a partir de `idMembersWatching`/`idMembersVoted` |
| Labels | Coberto | Sim |
| Datas | Coberto | Sim |
| Campos derivados | Coberto | Sim |
| Evidencias | Coberto | Sim, descricao + anexos |

## Dependencias remanescentes do legado

O modelo agora suporta a informacao, mas varios consumidores ainda leem diretamente o legado:

- `analytics.adapters`;
- `analytics.services.builders`;
- `apps.intelligence.services.report_query.*`;
- `apps.intelligence.providers.trello`;
- `apps.intelligence.services.timeline.engine`;
- `apps.intelligence.services.risk_engine.scorer`;
- `apps.intelligence.services.bottleneck_detector.detector`;
- `apps.intelligence.services.communication_analysis.analyzer`;
- `apps.intelligence.services.operational_score.scorer`;
- `apps.intelligence.services.kpi.engine`.

Essas dependencias estao detalhadas em `docs/CANONICAL_CONSUMERS.md`.

## Blockers

1. Coleta canonica ainda nao traz tudo por padrao.

O cliente canonico atual busca cards/listas/board, mas nao busca actions, comments, attachments ou checklists completos em chamadas dedicadas.

2. Consumers ainda esperam ORM legado.

Muitos consumidores recebem `Card`, `Action`, `CardStatusHistory` ou `CardRecord` derivado do legado.

3. Datas de conclusao e historico precisam de metodologia unica.

O legado usa combinacoes de `dueComplete`, status/lista, `CardStatusHistory` e actions. O canonico precisa reproduzir isso antes de substituir consumers.

4. Equivalencia de motores ainda precisa de etapa dedicada.

Nesta sprint foram criados testes de representacao/equivalencia factual do card. A equivalencia completa de narrativa, discovery e decisoes depende de migrar leitores, sem alterar os motores.

## Testes criados

Arquivo:

- `apps/integrations/tests/test_canonical_equivalence.py`

Cobertura:

- compara fatos de um mesmo card entre expectativa legada e mapper canonico;
- valida roundtrip de payload canonico rico;
- documenta fronteira atual: metricas/eventos/riscos/classificacao possuem fatos canonicos; narrativa/discovery/decisoes ainda nao sao recalculadas a partir do canonico nesta sprint.

## Diferencas documentadas

| Area | Status |
| --- | --- |
| Metricas | Fatos necessarios representados em `derived_fields`, `dates`, `checklists`, `movements` |
| Eventos | Representados em `actions`, `history`, `movements` |
| Riscos | Sinais estruturados da descricao representados |
| Classificacao | Texto, labels e descricao estruturada representados |
| Narrativa | Nao recalculada nesta sprint |
| Discovery | Nao recalculado nesta sprint |
| Decisoes | Nao recalculadas nesta sprint |

## Proximos passos

1. Ampliar coleta canonica Trello para actions, checklists completos e attachments.
2. Criar bridge `CanonicalTaskRecord -> CardRecord/ActionRecord`.
3. Rodar comparacao lado a lado em board real.
4. Migrar consumidores por feature flag.
5. Manter legado como fallback ate equivalencia operacional completa.

## Conclusao

A consolidacao do modelo foi realizada sem remover compatibilidade e sem alterar motores analiticos. A dependencia do legado deixa de ser um limite de modelo e passa a ser um plano de migracao de consumidores e coleta.

