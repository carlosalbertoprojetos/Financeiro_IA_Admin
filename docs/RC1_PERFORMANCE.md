# RC1 Performance

Data: 2026-06-27

## Metodologia

Ambiente local controlado com `EOR_TESTING=true`, banco de teste criado via Django test runner e rollback ao final. Foram gerados boards temporarios com cards Trello canonicos e executado:

- relatorio executivo;
- export Markdown;
- export PDF;
- export PPTX.

Metrica coletada:

- tempo total;
- pico de memoria via `tracemalloc`;
- quantidade de queries capturadas;
- cards retornados.

## Resultado

| Board | Cards | Tempo total | Pico memoria | Queries capturadas | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| Pequeno | 10 | 6.620,79 ms | 4,96 MB | 1.224 | PASS |
| Medio | 50 | 26.019,98 ms | 10,42 MB | 5.144 | PASS |
| Grande local | 150 | 76.138,94 ms | 20,12 MB | 1.605* | PASS |

`*` O Django emitiu warning de limite de query logging acima de 9.000 queries durante o teste grande local; portanto o numero capturado para 150 cards nao representa o total real.

## Observacao Importante

Uma tentativa com 500 cards excedeu 120 segundos no ambiente local. Isso nao quebrou a suite automatizada, mas indica gargalo de performance para boards grandes antes de piloto com alto volume.

## Diagnostico

Status RC1: aprovado para piloto controlado com boards pequenos/medios.

Risco: boards grandes podem ter latencia alta por volume de queries e recomputacao repetida entre relatorio e exports.

## Recomendacoes Sem Nova Feature

- Usar `use_cache=True` em fluxos de usuario quando aplicavel.
- Rodar pilotos iniciais com boards pequenos/medios.
- Monitorar tempo de geracao de relatorio por board.
- Antes de producao ampla, otimizar queries do report engine e reaproveitar resultado entre exports.
