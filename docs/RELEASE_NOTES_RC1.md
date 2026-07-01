# Release Notes RC1

Data: 2026-06-27

## Novidades

RC1 nao adiciona funcionalidades novas. O foco foi estabilidade, confiabilidade e preparacao para piloto.

## Correcoes

- Corrigida incompatibilidade de `JSONField__contains` com SQLite nos caminhos de dashboards e relatorio diario de piloto.
- Corrigida extracao do evento `ANALYSIS_PERFORMED` para textos contendo `Análise realizada`.
- Restabelecido teste de refresh de analytics do Trello worker apos correcao do caminho de analytics.

## Melhorias

- Suite completa estabilizada: 469/469 testes aprovados.
- Quality gate e baseline confirmados.
- Documentacao RC1 adicionada.
- Performance e stress controlados documentados.
- API simples de acompanhamento de piloto exposta em `GET /api/pilot/dashboard/?board_id=<BOARD_ID>`.

## Mudancas Internas

- Filtros JSON portaveis movidos para avaliacao Python em pontos especificos.
- Regex de Description Intelligence ampliada sem criar novo tipo de evento.

## Breaking Changes

Nenhum breaking change intencional.

## Limitacoes Conhecidas

- PostgreSQL local em `localhost:5433` nao esta disponivel neste ambiente.
- Teste de performance local com 500 cards excedeu 120 segundos.
- Stress com SQLite pode emitir lock em thread concorrente, embora a suite finalize PASS.
- Redis, workers e scheduler reais precisam validacao em staging.
