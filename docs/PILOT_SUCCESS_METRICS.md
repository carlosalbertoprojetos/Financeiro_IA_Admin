# Pilot Success Metrics

Data: 2026-06-27

## Metricas Obrigatorias

| Metrica | Como medir | Fonte | Meta inicial |
| --- | --- | --- | --- |
| Tempo economizado na analise | Minutos estimados pelo gestor antes/depois de cada relatorio | Feedback humano | >= 30 min/semana |
| Riscos identificados | Total de decisoes/riscos priorizados com evidencia | `DecisionRecord`, relatorios | >= 3 |
| Decisoes recomendadas | Sugestoes geradas no periodo | `DecisionRecord` | >= 5 |
| Decisoes aceitas | Feedback `ACCEPTED` | `DecisionFeedbackRecord` | >= 60% aceitas ou modificadas |
| Decisoes rejeitadas | Feedback `IGNORED` | `DecisionFeedbackRecord` | Registrar 100% com motivo |
| Melhoria de SLA | Comparar SLA antes/depois | Board/relatorios | Tendencia positiva |
| Reducao de backlog | Comparar cards abertos antes/depois | Board/relatorios | Tendencia positiva |
| Reducao de retrabalho | Eventos/reaberturas/retrabalho observados | Board/feedback | Tendencia positiva |
| Satisfacao do gestor | Nota 1-5 por semana | Formulario de feedback | >= 4 |
| Valor percebido | Nota 1-5 e comentario qualitativo | Formulario de feedback | >= 4 |

## Metricas de Controle

- Relatorios gerados.
- Quality score do relatorio.
- DecisionValueScore.
- Follow-ups de impacto medidos.
- Acoes executadas manualmente.
- Acoes bloqueadas.
- Erros operacionais.

## Regra de Evidencia

Nenhuma metrica de impacto deve ser marcada como realizada sem evidencia observada. Quando nao houver dado, usar `sem dados suficientes`.

## Dashboard

Endpoint operacional:

```text
GET /api/pilot/dashboard/?board_id=<BOARD_ID>
```

O endpoint mostra uso, decisoes, riscos, impacto observado e scores a partir de dados persistidos existentes.
