# RC1 Root Cause Analysis

Data: 2026-06-27

## Causa Raiz 1 - Lookup JSON nao portavel

### Sintoma

Varios testes falhavam com:

```text
django.db.utils.NotSupportedError: contains lookup is not supported on this database backend
```

### Causa raiz

O codigo usava `JSONField__contains` em caminhos executados pela suite local/CI com SQLite. Esse lookup e suportado em PostgreSQL, mas nao pelo backend SQLite usado em `EOR_TESTING`.

### Arquivos corrigidos

- `apps/dashboards/services/canonical_metrics.py`
- `apps/intelligence/services/pilot/report_generator.py`

### Correcao aplicada

Os filtros relacionais continuam no banco. Apenas o predicado de JSON foi movido para Python:

- `metadata.closed is True` para excluir tasks encerradas;
- `original_action_json.execution_mode == "SEMI_AUTOMATIC"` para contar sugestoes ignoradas criticas.

### Por que nao e sintoma

A regra de negocio foi preservada. A correcao remove a dependencia de um operador especifico de backend em caminhos que precisam rodar em CI/local.

## Causa Raiz 2 - Regex incompleta para evento de analise

### Sintoma

`ANALYSIS_PERFORMED` nao era extraido de uma descricao contendo:

```text
Análise realizada nos logs app.log
```

### Causa raiz

O extrator reconhecia formas como `analisado/analisada`, mas nao a palavra `análise`.

### Arquivo corrigido

- `apps/intelligence/services/description_intelligence/event_extractor.py`

### Correcao aplicada

O padrao de `ANALYSIS_PERFORMED` passou a reconhecer `análise` e `analise`, alem das formas ja existentes.

## Causa Raiz 3 - Worker dependia de analytics quebrado

### Sintoma

`analytics_refreshed` ficava `0` no teste de `ingestion.completed`.

### Causa raiz

O refresh de analytics chamava o caminho de dashboards que falhava antes por `metadata__contains`.

### Correcao aplicada

Resolvida pela Causa Raiz 1. O worker nao exigiu alteracao propria.

## Validacao Pos-Correcao

- Teste de infrastructure/scope: PASS.
- Teste de report generator: PASS.
- Teste de Trello worker: PASS.
- Teste de Description Intelligence: PASS.
- Suite completa: 469/469 PASS.
