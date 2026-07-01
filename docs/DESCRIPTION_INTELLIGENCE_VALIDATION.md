# Description Intelligence Validation

## Objetivo

Transformar a descricao dos cards Trello em fonte primaria de inteligencia operacional para Semantic Layer, Timeline, KPIs, Risk Engine, OLE, BVE e relatorios executivos.

## Implementacao

Modulo criado:

`apps/intelligence/services/description_intelligence/`

Componentes:

- `parser.py`: leitura integral de texto, markdown, headings, bullets, links, tabelas, blocos de codigo e pares chave-valor.
- `classifier.py`: classificacao multi-categoria com confianca e evidencias.
- `entity_extractor.py`: extracao de IPs, hosts, URLs, tickets, versoes, arquivos, bancos, protocolos, ambientes e entidades por chave.
- `event_extractor.py`: deteccao de problema, analise, acao, teste, resultado, homologacao, implantacao, rollback e encerramento.
- `quality_score.py`: Description Quality Score em escala 0-100.
- `summary.py`: resumo executivo expandido, KPIs, dashboards e agregacao por board.

## Regras criticas atendidas

- Nenhum resumo e produzido antes da extracao estruturada.
- Todo campo extraido carrega `source`, `line` e `evidence`.
- Classificacoes sempre possuem `confidence`.
- Descricao vazia retorna classificacao `Outra`, sem entidades/eventos inferidos.
- Recomendacoes e dashboards usam apenas evidencias extraidas.

## Integracoes realizadas

- Semantic Layer: `map_card_to_entity` inclui `description_intelligence` no metadata.
- Categoria semantica pode vir da descricao quando nao ha prefixo ou label forte.
- Risk flags incluem bloqueios, dependencias e impacto encontrados na descricao.
- KPI Engine: `compute_board_kpis` inclui KPIs avancados do DIE.
- Executive Report: nova secao `15_description_intelligence` com resumo expandido, classificacao, indicadores, dashboards, qualidade e rastreabilidade.
- Timeline: `persist_description_events` permite registrar eventos extraidos da descricao em `TimelineEvent`.

## KPIs criados

- Infrastructure Workload Index
- Maintenance Index
- Incident Density
- Correction Rate
- Improvement Rate
- Preventive vs Corrective Ratio
- Operational Complexity Score
- Description Completeness
- Operational Documentation Score
- Knowledge Capture Score

## Dashboards gerados

- Infraestrutura
- Suporte
- Projetos
- Melhorias
- Incidentes
- Preventiva
- Corretiva
- Executivo

Cada dashboard contem KPIs, timeline, heatmap de qualidade por categoria, top categorias, top sistemas e top riscos baseados na descricao.

## Comparativo antes/depois

| Dimensao | Antes | Depois |
| --- | --- | --- |
| Fonte principal | Titulo, labels, membros, datas, movimentacoes | Descricao completa + fontes anteriores |
| Rastreabilidade | Parcial | Linha e evidencia por campo extraido |
| Categorias | Inferidas principalmente por titulo/label | Multi-categoria por descricao com confianca |
| Entidades operacionais | Limitadas | IP, host, sistema, cliente, ambiente, ticket, arquivo, URL, banco, protocolo |
| Eventos | Trello actions | Trello actions + eventos narrados na descricao |
| Qualidade documental | Nao medida | Description Quality Score |
| Relatorio executivo | Resumo operacional geral | Resumo expandido objetivo/contexto/problema/solucao/resultado/impacto |

## Validacao pendente em board real

Executar em ambiente com PostgreSQL e board sincronizado:

```powershell
.\.venv\Scripts\python.exe manage.py test apps.intelligence.tests.test_description_intelligence
.\.venv\Scripts\python.exe manage.py shell
```

No shell:

```python
from integrations.trello.models import Board, Card
from apps.intelligence.services.description_intelligence.summary import aggregate_description_intelligence

board = Board.objects.get(trello_id="BOARD_REAL")
cards = list(Card.objects.filter(board=board, is_removed=False)[:500])
report = aggregate_description_intelligence(cards)
print(report["cards_analyzed"])
print(report["categories"])
print(report["entities_by_type"])
print(report["events_by_type"])
print(report["avg_description_quality_score"])
```

Metricas a comparar:

- Quantidade de informacao extraida.
- Quantidade de entidades.
- Quantidade de eventos.
- Quantidade de categorias.
- Quantidade de KPIs.
- Quantidade de insights e dashboards populados.

## Status

Implementado no codigo. A validacao automatizada Django depende do PostgreSQL local ativo em `localhost:5433`; na execucao atual o banco recusou conexao.
