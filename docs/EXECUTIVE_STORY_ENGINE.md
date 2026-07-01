# Executive Story Engine

## Objetivo

O Executive Story Engine transforma KPIs, enriquecimento analitico, narrativa executiva, discovery insights, riscos e recomendacoes em uma historia executiva coerente.

Ele responde:

- qual foi a historia operacional do periodo;
- o que mudou;
- o que explica o resultado;
- quais poucos fatores mais impactaram;
- o que a gestao deve decidir agora;
- o que fazer primeiro.

## Localizacao

```text
apps/intelligence/services/report_query/engine/executive_story.py
```

Integrado em:

```text
apps/intelligence/services/report_query/engine/executor.py
apps/intelligence/services/report_query/exporters/formats.py
```

## Entrada

O motor recebe apenas dados ja calculados:

- summary;
- metrics;
- analytical_enrichment;
- executive_narrative;
- discovery;
- risks;
- recommendations.

Nao usa IA externa e nao inventa fatos. Se nao houver evidencia, a historia nao e gerada.

## Saida

```json
{
  "executive_story": {
    "headline": "",
    "period_story": "",
    "story_structure": {},
    "what_changed": [],
    "key_drivers": [],
    "root_causes": [],
    "business_implications": [],
    "priority_decisions": [],
    "decision_ready_summary": [],
    "action_plan": [],
    "story_confidence": 0,
    "executive_story_quality_score": {},
    "evidence_map": [],
    "generated": true
  }
}
```

## Estrutura obrigatoria

`story_structure` segue a sequencia:

1. Contexto do periodo
2. Principais mudancas
3. Fatores que explicam o resultado
4. Causas provaveis
5. Impactos operacionais
6. Riscos se nada mudar
7. Oportunidades
8. Decisoes prioritarias
9. Plano de acao

Cada secao contem resumo e evidencias.

## Top 3 Executive Drivers

`key_drivers` seleciona no maximo tres fatores principais.

Criterios:

- impacto;
- severidade;
- recorrencia;
- evidencia;
- risco futuro.

Cada driver contem:

- titulo;
- explicacao;
- evidencias;
- impacto;
- acao recomendada;
- confianca.

## Decision Ready Summary

`decision_ready_summary` traz ate tres decisoes recomendadas.

Cada decisao contem:

- decisao;
- motivo;
- evidencia;
- consequencia de nao agir;
- urgencia;
- dono sugerido;
- prazo sugerido.

## ExecutiveStoryQualityScore

Escala: 0 a 100.

Criterios:

- clareza;
- evidencia;
- priorizacao;
- conexao causa-impacto;
- decisoes acionaveis;
- ausencia de excesso de informacao.

## Evidence Map

`evidence_map` liga cada afirmacao da historia a uma fonte:

- insights narrativos;
- highlights de discovery;
- descobertas;
- riscos;
- recomendacoes;
- metricas de SLA;
- metricas de qualidade.

Se o mapa fica vazio, `generated=false`.

## Exports

JSON inclui o bloco completo `executive_story`.

Markdown abre com:

- Historia Executiva;
- Top 3 Drivers;
- Decisoes Prioritarias;
- Plano de Acao.

PDF prioriza headline, historia do periodo, drivers e decisoes antes dos blocos analiticos.

PPTX outline abre com:

1. Historia Executiva
2. Top 3 Drivers
3. Decisoes Prioritarias
4. Riscos se Nada Mudar
5. Plano de Acao

## Guardrails

- Historia sem evidencia nao e gerada.
- No maximo tres drivers.
- Decisoes precisam de evidencia.
- Plano de acao e criado quando ha risco ou decisao.
- Score sempre retorna criterios e justificativa.
- O motor e deterministico e local.
