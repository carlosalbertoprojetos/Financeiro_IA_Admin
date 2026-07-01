# Enriquecimento dos Relatorios: Antes e Depois

## Antes

O pipeline `report_query` retornava:

- metadados do filtro;
- dados do template solicitado;
- metricas basicas solicitadas;
- agrupamentos opcionais;
- lista de cards;
- exportacao no formato escolhido.

O resultado era funcional para consulta, mas pouco explicativo para decisao executiva. O usuario precisava inferir quais cards eram criticos, quais evidencias sustentavam uma recomendacao e se o relatorio tinha dados suficientes.

## Depois

O mesmo pipeline agora adiciona `analytical` sem quebrar rotas ou payloads existentes.

Novos blocos:

- `analytical.activity_classification`: categoria, confianca e evidencias por card.
- `analytical.metrics_pack.volume`: distribuicao por atividade, etiqueta, lista e status.
- `analytical.metrics_pack.time`: idade media, tempo medio de conclusao e cards parados.
- `analytical.metrics_pack.sla`: compliance, vencidos e itens em risco.
- `analytical.metrics_pack.quality`: descricoes ruins, cards sem dono, sem prazo e checklists pendentes.
- `analytical.metrics_pack.communication`: comentarios, cards sem comentario e evidencia de decisao.
- `analytical.metrics_pack.workload`: carga e risco medio por responsavel.
- `analytical.metrics_pack.trends`: volume por semana e mes.
- `analytical.metrics_pack.risks`: cards criticos, motivos e proxima acao.
- `analytical.recommendations`: recomendacoes priorizadas com evidencia.
- `analytical.quality`: score do relatorio, justificativa, secoes ausentes e sugestoes.

Campos de topo adicionados:

- `report_quality_score`
- `report_quality_label`
- `missing_sections`
- `improvement_suggestions`

## Exportacoes

| Formato | Antes | Depois |
| --- | --- | --- |
| JSON | Resultado bruto | Resultado completo com camada analitica |
| CSV | `card_id`, titulo e status | Inclui atividade, confianca, risco, qualidade, comentarios, checklist e proxima acao |
| Excel | CSV simplificado como `.xls` | Mesmo conteudo enriquecido do CSV |
| Markdown | Dump do template | Score, indicadores, recomendacoes e resumo |
| PDF | Lista simples de cards | Score, resumo analitico, recomendacoes e cards com risco/atividade |
| PPTX | Outline minimo | Outline com qualidade, metricas e recomendacoes |

## Impacto esperado

- Menos interpretacao manual do relatorio.
- Melhor rastreabilidade entre recomendacao e evidencia.
- Identificacao rapida de cards vencidos, parados, sem dono ou com descricao ruim.
- Comparacao objetiva da utilidade de um relatorio pelo `report_quality_score`.
- Menos falso insight, porque baixa evidencia reduz confianca e aparece como limitacao.

## Componentes alterados

- `apps/intelligence/services/report_query/engine/analytical_enrichment.py`
- `apps/intelligence/services/report_query/engine/executor.py`
- `apps/intelligence/services/report_query/exporters/formats.py`
- `apps/intelligence/tests/test_report_analytical_quality.py`

## Estrategia de compatibilidade

- Nenhuma rota existente foi removida.
- O payload de entrada nao mudou.
- Campos antigos continuam presentes.
- Novos campos sao aditivos.
- Exportadores mantem `content_base64`, `content_type`, `filename` e `size_bytes`.
