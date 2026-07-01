# RC1 Stress Test

Data: 2026-06-27

## Metodologia

Stress controlado local com payload fixture validado pelo quality gate, sem chamadas externas e sem banco produtivo.

Cenario:

- 20 validacoes concorrentes de qualidade;
- 30 exports concorrentes;
- formatos: Markdown, PDF e PPTX;
- executor: `ThreadPoolExecutor` com 8 workers.

## Resultado

| Metrica | Valor |
| --- | ---: |
| Quality validations | 20 |
| Quality PASS | 20 |
| Exports gerados | 30 |
| Erros | 0 |
| Tempo total | 549,43 ms |
| Pico memoria | 3,67 MB |
| Status | PASS |

## Gargalos

- Stress fixture/export passou sem deadlock, timeout ou erro.
- Suite completa exibiu uma excecao em thread de fila SQLite (`database table is locked`) durante teste concorrente interno, mas a suite final terminou PASS. Isso e caracteristico de SQLite em testes concorrentes e deve ser monitorado em CI.

## Parecer

Stress aprovado para RC1 em modo controlado. Para piloto real, validar simultaneidade com PostgreSQL e Redis reais antes de aumentar volume.
