# Validacao do Discovery Insights Engine

## Validacao de workspace

Comando obrigatorio executado antes da sprint:

```powershell
python manage.py validate_eor_workspace --json
```

Resultado:

- workspace: `EOR`
- status: `ready`
- model_version: `1.1`
- checks: 27
- failures: 0
- warnings: 0

## Escopo validado

A sprint alterou apenas o pipeline de relatorios:

- `apps/intelligence/services/report_query/engine/discovery_engine.py`
- `apps/intelligence/services/report_query/engine/executor.py`
- `apps/intelligence/services/report_query/exporters/formats.py`
- testes de relatorio
- documentacao

Nao foram alterados:

- multi-tenant;
- licensing;
- marketplace;
- connectors;
- release gate.

## Cenarios de teste

### Board com sinais fortes

Massa ficticia com:

- 8 cards;
- incidentes repetitivos;
- cards vencidos;
- cards sem responsavel;
- descricoes vazias;
- checklists pendentes;
- cards parados;
- comentarios concentrados;
- tendencia semanal de aumento.

Validacoes:

- descobertas possuem evidencia;
- anomalias possuem evidencia;
- oportunidades possuem evidencia;
- correlacoes respeitam amostra minima;
- correlacoes trazem coeficiente, confianca e limitacoes;
- previsoes possuem tendencia observada e base.

### Board limpo e pequeno

Massa ficticia com:

- 3 cards;
- responsavel definido;
- prazo futuro;
- descricao completa;
- checklist completo;
- comentario registrado.

Validacoes:

- nenhuma anomalia falsa;
- nenhuma correlacao sem amostra minima.

## Comandos de validacao

```powershell
$env:EOR_TESTING='true'; python manage.py test apps.intelligence.tests.test_report_discovery_engine
$env:EOR_TESTING='true'; python manage.py test apps.intelligence.tests.test_report_query apps.intelligence.tests.test_report_query_metrics apps.intelligence.tests.test_report_analytical_quality apps.intelligence.tests.test_report_discovery_engine
$env:EOR_TESTING='true'; python manage.py check
python -m compileall apps\intelligence\services\report_query\engine\discovery_engine.py apps\intelligence\services\report_query\engine\executor.py apps\intelligence\services\report_query\exporters\formats.py apps\intelligence\tests\test_report_discovery_engine.py
```

## Criterios de aceite cobertos

- Nenhuma descoberta sem evidencia.
- Nenhuma correlacao sem amostra minima.
- Nenhuma previsao sem tendencia observada.
- Nenhuma anomalia falsa em board limpo.
- Exports Markdown e PPTX incluem discovery.
- JSON inclui o bloco `discovery` completo.

## Limitacoes

- Correlacoes sao estatisticas simples e nao provam causalidade.
- Detecao de sistemas/projetos depende de termos explicitos nos titulos.
- Tendencias dependem de distribuicao temporal no recorte filtrado.
- O motor e deterministico; nao interpreta contexto fora dos campos ja disponiveis.
