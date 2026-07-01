# Executive Report Narrative

## Objetivo

A camada de narrativa executiva transforma o pacote analitico do `report_query` em um relatorio interpretavel para decisao gerencial. Ela responde:

- o que aconteceu;
- por que importa;
- qual causa provavel explica o padrao;
- qual impacto operacional e de SLA existe;
- qual decisao a gestao deve tomar.

## Escopo

A implementacao fica restrita ao pipeline de relatorios:

- `apps/intelligence/services/report_query/engine/executive_narrative.py`
- `apps/intelligence/services/report_query/engine/executor.py`
- `apps/intelligence/services/report_query/exporters/formats.py`

Nao altera multi-tenant, licensing, marketplace, conectores ou release gate.

## Entrada

A narrativa consome apenas dados ja calculados em `analytical`:

- `metrics_pack.sla`
- `metrics_pack.quality`
- `metrics_pack.communication`
- `metrics_pack.workload`
- `metrics_pack.time`
- `metrics_pack.risks`
- `analytical.recommendations`
- `activity_classification.cards`

Nao ha chamada externa de IA e nao ha inferencia sem metrica ou evidencia.

## Saida

O resultado do `execute_report_query` passa a incluir:

```json
{
  "executive_narrative": {
    "sections": {},
    "insights": [],
    "root_cause_hypotheses": [],
    "management_decisions": [],
    "next_actions": [],
    "executive_readability_score": {}
  }
}
```

## Secoes narrativas

1. Diagnostico Executivo
2. Principais Achados
3. Causas Provaveis
4. Impacto Operacional
5. Impacto em Prazo/SLA
6. Riscos Prioritarios
7. Recomendacoes Acionaveis
8. Decisoes Necessarias da Gestao
9. Proximas Acoes

Cada secao contem:

- `title`
- `summary`
- `evidence`

## Priorizacao de insights

Cada insight contem:

- `title`
- `severity`
- `metric_source`
- `evidence`
- `affected_area`
- `business_impact`
- `recommended_action`
- `confidence`

A ordenacao usa, nesta ordem:

1. risco;
2. impacto;
3. urgencia;
4. recorrencia.

## Hipoteses de causa raiz

As hipoteses sao deterministicas e baseadas em combinacoes simples:

- atraso aberto + cards parados -> possivel gargalo de decisao;
- cards sem responsavel -> falha de triagem;
- descricao incompleta + checklist pendente -> baixa qualidade de especificacao;
- comentarios sem decisao -> comunicacao inconclusiva;
- risco concentrado por tipo -> possivel gargalo especializado.

Cada hipotese contem:

- hipotese;
- evidencias;
- confianca;
- como validar;
- acao recomendada.

## Decisoes da gestao

O bloco `management_decisions` sugere decisoes com:

- decisao;
- motivo;
- impacto esperado;
- urgencia;
- dono sugerido;
- prazo sugerido.

Exemplos cobertos:

- repriorizar cards criticos;
- redistribuir carga;
- definir SLA ou data alvo;
- exigir descricao minima;
- melhorar dados antes de decisao estrutural quando faltam evidencias.

## ExecutiveReadabilityScore

Escala: 0 a 100.

Criterios:

- clareza do diagnostico;
- presenca de recomendacoes;
- presenca de decisao sugerida;
- ligacao entre metrica e conclusao;
- ausencia de secoes narrativas vazias;
- linguagem executiva com validacao de causa.

O score retorna:

- `score`
- `label`
- `criteria`
- `justification`

## Exports

- JSON: inclui o bloco completo `executive_narrative`.
- Markdown: adiciona `Narrativa Executiva` com secoes e evidencias.
- PDF: inclui qualidade, legibilidade, diagnostico, SLA e decisao.
- PPTX outline: gera cinco slides logicos:
  - Diagnostico
  - KPIs
  - Riscos
  - Decisoes recomendadas
  - Proximas acoes

## Guardrails

- Nenhuma narrativa e criada sem evidencia ou metrica.
- Nenhum insight entra sem `metric_source`.
- Hipoteses sempre explicam como validar.
- Decisoes sempre indicam dono e prazo sugerido.
- Secoes vazias recebem fallback explicito de baixa evidencia.
- A camada e deterministica e local.
