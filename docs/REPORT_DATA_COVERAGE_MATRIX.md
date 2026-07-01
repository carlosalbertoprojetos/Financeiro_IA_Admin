# Matriz de Cobertura de Dados dos Relatorios

| Dimensao | Fonte atual | Uso no relatorio | Cobertura |
| --- | --- | --- | --- |
| Volume | `Card` filtrado por board | total, status, lista, etiqueta e tipo de atividade | coberto |
| Tipo de atividade | titulo, descricao, status, etiquetas e comentarios | classificacao heuristica com confianca e evidencia | coberto |
| Tempo | criacao, conclusao, ultima atividade | idade media, tempo medio de conclusao e cards parados | coberto |
| SLA | `due_at`, `completed_at`, status | vencidos, risco em 48h e compliance | coberto |
| Qualidade | descricao, responsavel, prazo, checklist | descricoes incompletas, cards sem dono, pendencias | coberto |
| Comunicacao | `Action.commentCard` | comentarios totais, media e cards sem comentario | coberto |
| Risco | `assess_card_risk` e evidencias operacionais | cards criticos, risco por tipo e probabilidade de atraso | coberto |
| Carga | assignees + risco por card | cards e risco medio por responsavel | coberto |
| Tendencia | data de criacao | volume por semana e mes | coberto |
| Recomendacoes | riscos, SLA, qualidade e confianca | acoes priorizadas com evidencias | coberto |
| Limitacoes | secoes sem dados suficientes | secoes ausentes e sugestoes de melhoria | coberto |

## Secoes analiticas padrao

O score de qualidade considera 16 secoes:

1. Resumo executivo
2. Contexto operacional
3. Volume e distribuicao
4. Tipos de atividade
5. Tempo e ciclo
6. SLA e atrasos
7. Riscos
8. Gargalos
9. Qualidade operacional
10. Comunicacao
11. Carga por responsavel
12. Tendencias
13. Itens criticos
14. Recomendacoes
15. Evidencias
16. Limitacoes

## Regras de evidencia

- Nenhuma recomendacao deve ser criada sem evidencia.
- Todo score deve retornar justificativa.
- Textos vazios geram baixa qualidade, nao insight falso.
- Baixa confianca de classificacao aparece no payload e no card row.
- As heuristicas ficam concentradas em `apps/intelligence/services/report_query/engine/analytical_enrichment.py`.
