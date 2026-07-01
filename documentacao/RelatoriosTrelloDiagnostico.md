# Diagnostico dos Relatorios Trello

Data do diagnostico: 2026-06-27

## Objetivo

Este documento registra a leitura inicial do projeto EOP/TIP antes de qualquer evolucao funcional nos relatorios Trello. O objetivo e preservar compatibilidade com os relatorios existentes e orientar a evolucao incremental da descricao dos cards como fonte estruturada de inteligencia operacional.

## Gate de workspace

Antes da leitura e de qualquer alteracao, foi executado:

```powershell
python manage.py validate_eor_workspace --json
```

Resultado: workspace `EOR`, status `ready`, versao de modelo `1.1`, 27 checks, 0 falhas e 0 avisos.

## Arquitetura atual

O projeto possui duas trilhas principais de dados Trello:

1. Pipeline legado Trello

- Entrada HTTP/API: `integrations/trello/client.py`
- Sync persistente: `integrations/trello/services/sync.py`
- Normalizacao simples: `integrations/trello/normalizers.py`
- Modelos ricos: `integrations/trello/models.py`
- Analytics legado: `analytics/adapters.py`, `analytics/engine/metrics.py`, `analytics/services/builders.py`
- Relatorios enriquecidos: `apps/intelligence/services/report_query/`
- PDF legado/executivo: `reports/engine/pdf_builder.py`

2. Pipeline canonico/plataforma

- Cliente Trello novo: `apps/integrations/trello/client.py`
- Adapter multi-provider: `apps/integrations/trello/adapter.py`
- Mapper para task canonica: `apps/integrations/trello/mapper.py`
- Persistencia canonica: `apps/integrations/models.py`
- Engine incremental: `apps/integrations/core/ingestion_engine.py`
- Dashboard canonico: `apps/dashboards/services/canonical_metrics.py`
- Analytics canonico: `apps/dashboards/services/canonical_analytics.py`
- Relatorio PDF canonico: `apps/dashboards/services/canonical_report.py`, `apps/reports/views.py`

Essas trilhas coexistem. O pipeline legado tem mais profundidade operacional porque persiste actions, historico, snapshots e relacionamentos ricos. O pipeline canonico e mais simples, voltado a portal/multi-provider, usando `CanonicalTaskRecord` com `metadata`.

## Fluxo de dados atual

### Fluxo legado

```text
Trello REST API
  -> integrations.trello.client.TrelloClient
  -> integrations.trello.services.sync.sync_board
  -> Board, BoardList, Member, Card, Action, CardStatusHistory, EntityHistory, Snapshot
  -> analytics.adapters
  -> analytics.engine.metrics
  -> apps.intelligence.services.report_query
  -> exporters JSON/CSV/Excel/Markdown/PDF/PPTX ou reports.engine.pdf_builder
```

O sync legado coleta board, listas, cards, membros e actions. Cards removidos sao marcados por diferenca entre a carga atual e os cards persistidos. Actions sao salvas como log imutavel e alimentam comunicacao, retrabalho e timeline.

### Fluxo canonico

```text
Trello REST API
  -> apps.integrations.trello.client.TrelloClient
  -> TrelloAdapter.fetch/fetch_incremental
  -> apps.integrations.trello.mapper.map_trello_payload
  -> CanonicalTask
  -> CanonicalTaskRecord
  -> apps.dashboards canonical metrics/analytics
  -> apps.reports executive PDF
```

O fluxo canonico coleta menos campos e transforma cada card em uma task com titulo, status, prazo, projeto e `metadata`. Ele preserva extensibilidade para outros provedores, mas ainda nao carrega membros, comments, actions, checklists completos ou estrutura interpretada da descricao.

## Onde a API do Trello e chamada

### Cliente legado

Arquivo: `integrations/trello/client.py`

Campos buscados:

- Board: `name`, `desc`, `url`, `closed`, `dateLastActivity`
- Listas: `name`, `pos`, `closed`
- Cards: `name`, `desc`, `idList`, `idBoard`, `idMembers`, `due`, `dueComplete`, `closed`, `labels`, `dateLastActivity`, `pos`, `url`, `shortUrl`, `idChecklists`, `badges`
- Membros: `username`, `fullName`
- Actions: `type`, `date`, `idMemberCreator`, `data`

Observacao: actions sao paginadas com `limit=1000` e `before`.

### Cliente canonico

Arquivo: `apps/integrations/trello/client.py`

Campos buscados:

- Board: `id`, `name`, `desc`, `url`, `closed`, `idOrganization`, `dateLastActivity`
- Listas: `id`, `name`, `pos`, `closed`, `idBoard`
- Cards: `id`, `name`, `desc`, `idList`, `idBoard`, `due`, `dueComplete`, `closed`, `labels`, `dateLastActivity`, `url`, `shortUrl`, `pos`
- Workspaces e membro autenticado para conexao/configuracao.

Observacao: o caminho canonico nao busca members por card, actions, comentarios, anexos ou checklists completos.

## Modelagem de cards

### Modelo legado

Arquivo: `integrations/trello/models.py`

`Card` possui:

- `trello_id`
- `board`
- `board_list`
- `title`
- `description`
- `status`
- `assignees`
- `due_at`
- `completed_at`
- `is_closed`
- `is_removed`
- `labels`
- `url`
- `position`
- `last_activity_at`
- `raw_json`

Pontos importantes:

- `description` preserva o texto bruto do Trello.
- `raw_json` preserva o payload original do card.
- `completed_at` hoje e derivado de `dueComplete` no normalizer, nao necessariamente da data real de conclusao por lista/action.
- `CardStatusHistory` registra mudancas de status/lista observadas no sync.
- `Action` preserva o historico bruto do Trello e permite extrair comentarios, movimentacoes e retrabalho.

### Modelo canonico

Arquivos: `apps/integrations/core/canonical.py`, `apps/integrations/models.py`

`CanonicalTask` e `CanonicalTaskRecord` possuem:

- `source_provider`
- `source_id`
- `title`
- `status`
- `project_id`
- `due_date`
- `metadata`

No mapper Trello, `metadata` recebe atualmente:

- `project_name`
- `project_url`
- `workspace_id`
- `list_id`
- `list_name`
- `closed`
- `due_complete`
- `url`
- `labels`

Limite atual: a descricao `desc` e coletada pelo cliente canonico, mas nao e persistida no `CanonicalTask.metadata`. Isso impede dashboards canonicos e relatorio canonico de usarem a descricao.

## Relatorios e dashboards atuais

### Dashboard canonico

Arquivo: `apps/dashboards/services/canonical_metrics.py`

Indicadores:

- total de tasks
- atrasadas
- buckets por status/lista
- provedores de origem
- tendencia de atualizacao dos ultimos 7 dias
- lista limitada de tasks vencidas

### Analytics canonico

Arquivo: `apps/dashboards/services/canonical_analytics.py`

Indicadores e insights:

- total de tasks Trello
- tasks atrasadas
- throughput de atualizacoes em 7 dias
- quantidade de listas/status
- maior concentracao por status
- aumento/reducao recente de atualizacoes

### Relatorio executivo canonico

Arquivos: `apps/dashboards/services/canonical_report.py`, `apps/reports/views.py`

Indicadores:

- total, abertos e concluidos
- throughput aproximado por tendencia de atualizacao
- delay rate aproximado com base em overdue
- diagnostico textual simples
- PDF via `reports.engine.pdf_builder`

Limite: o relatorio canonico nao usa actions, membros, comentarios, checklists completos nem descricao estruturada.

### Analytics legado

Arquivos: `analytics/engine/metrics.py`, `analytics/services/builders.py`

Indicadores:

- lead time
- cycle time
- throughput por dia/semana
- aging
- delay rate
- rework rate
- cards por responsavel
- gaps: atraso, aging alto, retrabalho, cards abertos sem responsavel
- prioridade inferida por etiqueta

### Report Query enriquecido

Arquivos principais: `apps/intelligence/services/report_query/`

Recursos:

- filtros por board, status, prioridade, checklist, risco, membros e outros
- templates executivo, operacional, SLA, riscos, produtividade, membro, equipe, etiqueta, cliente, prefixo e multidimensional
- metricas por card: lead time, cycle time, risk score, SLA
- agrupamentos por etiqueta, membro, status e prefixo
- camada analitica com volume, tempo, SLA, qualidade, comunicacao, workload, tendencias e riscos
- narrativa executiva, discovery, executive story e validação de qualidade
- exports JSON, CSV, Excel, Markdown, PDF e PPTX outline

## Indicadores existentes

### Por tarefa/card

Ja existem ou sao parcialmente calculados:

- lead time
- cycle time
- aging
- atraso/delay
- SLA textual por card
- risco operacional
- comentarios
- checklist total e pendente
- atividade/tipo por heuristica textual
- qualidade simples da descricao
- proxima acao sugerida
- retrabalho por actions de movimentacao retroativa
- evidencias simples para recomendacoes

### Por colaborador

Ja existem ou sao parcialmente calculados:

- cards por responsavel
- metricas por responsavel no analytics legado
- carga por membro no report query
- atrasados por membro
- risco medio por membro
- bloco de unassigned

Limite: eficiencia, eficacia, cumprimento de prazo por membro e produtividade por periodo ainda nao estao consolidados como contrato unico.

### Por equipe

Ja existem ou sao parcialmente calculados:

- volume total
- status/listas
- throughput
- lead/cycle medio no legado
- SLA/atrasos
- gargalos por aging/status
- distribuicao por etiquetas
- distribuicao por membros
- tendencia semanal/mensal de criacao

### Qualidade

Ja existem ou sao parcialmente calculados:

- descricao incompleta por tamanho
- media de score de descricao
- cards sem responsavel
- cards sem prazo
- cards com checklist pendente
- baixa confianca de classificacao
- cards sem comentario

Limite: ainda nao ha indice de completude baseado nas secoes preferenciais da descricao.

## Campos Trello usados

Campos usados de forma direta:

- nome do board
- descricao do board
- url do board
- status fechado do board
- lista/status do card
- nome/titulo do card
- descricao bruta do card
- membros/assignees no legado
- due date
- dueComplete
- closed
- labels
- posicao
- url/shortUrl
- last activity
- badges de checklist
- actions com tipo, data, criador e data payload
- comentarios via `Action.commentCard`
- movimentacoes via `Action.updateCard`

## Campos disponiveis, mas ignorados ou subutilizados

- `desc` no pipeline canonico: coletado, mas nao salvo no `metadata`.
- `idMembers` no pipeline canonico: nao e buscado no cliente novo nem mapeado.
- `idChecklists`/`badges`: legado usa parcialmente; canonico nao usa.
- Checklists completos: nao sao buscados explicitamente por chamada dedicada, exceto quando aparecem no `raw_json`; badges geram apenas itens sinteticos.
- Anexos: nao ha chamada nem modelagem dedicada para attachments.
- Comentarios: disponiveis no legado via actions, ausentes no canonico.
- Historico/movimentacoes: disponiveis no legado via actions/timeline, ausentes no canonico.
- Datas reais de movimentacao entre listas: parcialmente derivaveis de actions/timeline, mas nao normalizadas como um campo de card canonico.
- Data de criacao real do card: nao e explicitamente extraida do id Trello ou action `createCard`; o legado usa `created_at` do banco como aproximacao de ingestao.
- Data real de conclusao: hoje `completed_at` e derivado de `dueComplete`; conclusao por entrada em lista final precisa de actions/lista final.
- Solicitante: nao ha campo estruturado; so pode ser inferido de descricao, criador do card ou comentarios.
- Prioridade: inferida por labels/texto, sem contrato unico.

## Estado atual da inteligencia de descricao

Existe uma camada em `apps/intelligence/services/description_intelligence/` com:

- parser markdown generico com rastreabilidade por linha
- extracao de links, headings, bullets, tabelas, code blocks e key-values
- classificacao por categorias operacionais
- extracao de entidades
- extracao de eventos narrados
- score de qualidade
- agregacao por card/board
- testes em `apps/intelligence/tests/test_description_intelligence.py`

Essa camada e util, mas ainda nao atende integralmente ao contrato solicitado:

- nao retorna diretamente a estrutura preferencial `data_solicitacao`, `objetivo`, `contexto`, `atividades`, `resultado_esperado`, `riscos`, `criterios_conclusao`, `resultado_obtido`, `evidencias`, `links`, `metricas`, `raw_description`;
- reconhece headings markdown e key-values, mas nao todos os titulos soltos em caixa alta como secoes padronizadas;
- qualidade ainda e baseada em sinais gerais, nao nos 10 campos de completude da missao;
- nao esta integrada ao mapper canonico Trello;
- nao esta exposta como abas/secoes especificas de exportacao em todos os formatos.

## Limitacoes e riscos atuais

1. Dois pipelines Trello

Ha risco de implementar enriquecimento so no legado e deixar dashboards canonicos sem descricao, ou implementar so no canonico e quebrar os relatorios ricos que usam `integrations.trello.models.Card`.

2. Conclusao e datas

`completed_at` nao garante data real de conclusao. Lead time, cycle time, atraso e cumprimento de prazo dependem de metodologia clara.

3. Checklists incompletos

O legado usa badges ou `raw_json.checklists` quando disponivel, mas o cliente legado nao busca checklists completos por endpoint dedicado.

4. Comentarios e historico ausentes no canonico

O painel canonico nao tem base suficiente para varios indicadores pedidos: comentarios, retrabalho, movimentacoes e datas por lista.

5. Descricao pouco estruturada

Cards antigos podem ter descricoes livres, vazias ou incompletas. Parser deve retornar `None`, `0` ou lista vazia sem inferir fatos.

6. Risco de julgamento individual

Indicadores por colaborador precisam de nota metodologica e devem ser tratados como operacionais, nao como avaliacao absoluta de desempenho humano.

7. Exports possuem contratos diferentes

Report Query exporta JSON/CSV/Excel/Markdown/PDF/PPTX outline. O PDF canonico usa outro builder. Qualquer nova secao deve preservar campos existentes e adicionar dados de forma incremental.

8. Workspace com mudancas pre-existentes

O workspace possui muitas mudancas e arquivos nao rastreados. Evolucoes devem ser pequenas, revisadas por diff e sem reverter trabalho existente.

## Oportunidades de melhoria

### Parser de descricao estruturada

Criar uma camada especifica, reutilizavel, para o novo padrao:

```text
Data da Solicitação
OBJETIVO
CONTEXTO
ATIVIDADES
RESULTADO ESPERADO
RISCO
CRITÉRIO DE CONCLUSÃO
RESULTADO OBTIDO
EVIDÊNCIAS
```

Recomendacao: aproveitar `description_intelligence.parser` como base de rastreabilidade, mas criar um parser de contrato gerencial que produza a estrutura exata esperada.

### Normalizacao de card enriquecido

Criar uma camada intermediaria que nao substitua os modelos:

```text
Trello raw/ORM/canonical
  -> normalized/enriched card DTO
  -> metricas por tarefa
  -> agregacoes
  -> relatorios/exports
```

Essa camada deve aceitar tanto `integrations.trello.models.Card` quanto payload canonico quando possivel.

### Integração incremental ao legado

O melhor primeiro ponto de valor e o `Report Query`, porque ja possui cards, metrics pack, exports e narrativa. O enriquecimento deve adicionar campos aos `card_rows` e `analytical.metrics_pack.quality`, sem remover campos atuais.

### Integração incremental ao canonico

No mapper `apps/integrations/trello/mapper.py`, persistir descricao e sinais basicos no `metadata`:

- `description`
- `description_sections`
- `description_completeness_score`
- `links`
- `risks_count`
- `evidences_count`
- `checklist_total`
- `checklist_completed`
- `checklist_completion_percent` quando houver badges

Isso preserva `CanonicalTask` e evita migracao imediata.

### Metodologia de indicadores

Formalizar notas de calculo para:

- lead time
- cycle time
- data de conclusao
- atraso/antecipacao
- completude da documentacao
- produtividade por membro
- retrabalho

## Plano incremental de implementacao

### Fase 1 - Parser contratual da descricao

Arquivos provaveis:

- `apps/intelligence/services/description_intelligence/structured_sections.py`
- `apps/intelligence/tests/test_description_structured_sections.py`

Entregas:

- parser tolerante a variacoes de titulo
- estrutura de retorno exatamente compatível com a missao
- extracao de links, metricas, atividades, riscos, criterios e evidencias
- testes para descricao completa, incompleta, sem titulos, vazia, links, listas, riscos e evidencias multiplas

### Fase 2 - Normalizacao de card enriquecido

Arquivos provaveis:

- `apps/intelligence/services/trello_card_intelligence/normalizer.py`
- `apps/intelligence/tests/test_trello_card_normalizer.py`

Entregas:

- DTO/dict `NormalizedTrelloCard`
- compatibilidade com `integrations.trello.models.Card`
- uso de `raw_json`, labels, membros, badges, actions e descricao estruturada
- calculo de checklist total/concluido/percentual
- indice de completude conforme 10 campos da missao

### Fase 3 - Metricas por tarefa

Arquivos provaveis:

- `apps/intelligence/services/trello_card_intelligence/metrics.py`
- ajustes em `apps/intelligence/services/report_query/engine/post_processor.py`
- ajustes em `apps/intelligence/services/report_query/engine/analytical_enrichment.py`

Entregas:

- tempo de execucao quando houver dados
- lead/cycle time usando engine existente
- dias em atraso e antecipados
- complexidade por atividades
- comentarios, checklists, evidencias, riscos e anexos
- indicadores nulos quando o dado nao existir

### Fase 4 - Agregacoes por colaborador e equipe

Arquivos provaveis:

- `apps/intelligence/services/trello_card_intelligence/aggregations.py`
- ajustes nos templates `membro.py`, `equipe.py`, `executivo.py` e `operacional.py`

Entregas:

- cards concluidos, andamento, atrasados
- cumprimento de prazo
- volume e distribuicao por etiquetas
- demandas simultaneas
- retrabalho quando identificavel
- nota metodologica obrigatoria

### Fase 5 - Exports e dashboards

Arquivos provaveis:

- `apps/intelligence/services/report_query/exporters/formats.py`
- `apps/dashboards/services/canonical_metrics.py`
- `apps/dashboards/services/canonical_analytics.py`
- `apps/dashboards/services/canonical_report.py`

Entregas:

- novas secoes em Markdown/PDF/PPTX outline
- novas colunas CSV/Excel
- blocos: Indicadores por Tarefa, Colaborador, Equipe, Qualidade, Gestao, Cartoes Criticos e Dados Estruturados da Descricao
- compatibilidade com payloads atuais

### Fase 6 - Coleta Trello complementar

Arquivos provaveis:

- `integrations/trello/client.py`
- `integrations/trello/services/sync.py`
- `apps/integrations/trello/client.py`
- `apps/integrations/trello/mapper.py`

Entregas:

- avaliar custo de chamadas extras para checklists, attachments e comments
- evitar chamadas repetidas
- preferir actions ja coletadas no legado para comentarios/movimentacoes
- adicionar cache/normalizacao somente quando necessario

## Recomendacao de preservacao de compatibilidade

- Nao alterar o formato atual de `Card`, `CanonicalTask` ou exports existentes sem adicionar campos de forma opcional.
- Nao substituir `description_intelligence` existente; evoluir com novo modulo contratual e integrar gradualmente.
- Manter o pipeline legado como fonte de relatorios ricos enquanto o canonico nao captura actions/comments/checklists completos.
- Adicionar campos novos em `metadata`, `analytical`, `metrics_pack`, `cards` e exports com nomes estaveis.
- Para dados ausentes, retornar `None`, `0` ou lista vazia. Nao inferir fatos.
- Documentar metodologia dos indicadores por colaborador dentro do payload/export.

## Proximos passos recomendados

1. Implementar a Fase 1 isoladamente com testes unitarios.
2. Rodar testes focados de `description_intelligence`.
3. Integrar o parser ao `Report Query` sem alterar exports.
4. Adicionar campos aos exports em uma segunda mudanca.
5. So depois ampliar coleta Trello para checklists/anexos se a analise provar que os dados atuais sao insuficientes.

