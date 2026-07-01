# Relatório EXECUTIVO

## Índice

- Executive Brief
- História Executiva
- Scorecard Executivo
- Benchmark Interno
- Top 3 Drivers
- Decisões Prioritárias
- Plano de Ação
- Riscos, oportunidades e cenário provável

**Board:** Operacao Alpha - Suporte B2B
**Período:** LAST_7_DAYS
**Versão do relatório:** 1.0
**Cards:** 8
**Qualidade analítica:** 82 (bom)
**Legibilidade executiva:** 84 (bom)
**Inteligência do relatório:** 86 (executivo)
**Qualidade da história:** 88 (executivo)

## Executive Brief

> **Status geral:** Atencao executiva

A operacao de suporte B2B esta sob pressao de SLA: metade do recorte esta vencida, 37,5% dos cards nao possuem responsavel e a qualidade das descricoes limita a triagem.

| KPI | Valor | Tendência | Confiança |
| --- | ---: | --- | ---: |
| Cards analisados | 8 | estavel | 0.96 |
| SLA compliance | 50% | piorou | 0.84 |
| Cards vencidos | 4 | piorou | 0.88 |
| Sem responsavel | 3 | piorou | 0.8 |
| Descricoes incompletas | 5 | piorou | 0.82 |

**3 decisões:**
- Repriorizar incidentes vencidos ainda hoje.
- Definir responsaveis para todos os cards em ate 24h.
- Exigir descricao minima para novas demandas em 7 dias.

**3 riscos:**
- Incidente ERP financeiro vencido e sem replanejamento formal.
- Solicitacao de integracao fiscal sem responsavel definido.
- Descricoes incompletas aumentando dependencia de alinhamentos manuais.

**3 oportunidades:**
- Criar playbook para incidentes vencidos.
- Implantar checklist minimo de abertura.
- Revisar diariamente cards sem dono.

## História Executiva

**Headline:** Incidentes vencidos passaram a concentrar o risco executivo da operacao.

O periodo analisou 8 cards da operacao de suporte B2B. O principal desvio foi a concentracao de 4 cards vencidos, combinada a 3 cards sem responsavel e 5 descricoes incompletas. Isso reduz previsibilidade, aumenta risco de SLA e obriga a gestao a decidir hoje quais incidentes serao replanejados, quem assume cada demanda e qual padrao minimo de abertura sera exigido.

## Scorecard Executivo

**Score geral:** 72 (atencao)
**Confiança:** 0.84

| Dimensão | Score | Status | Evidência |
| --- | ---: | --- | --- |
| Saude Operacional | 68 | atencao | 4 de 8 cards vencidos |
| Qualidade | 62 | critico | 5 descricoes incompletas |
| Produtividade | 74 | bom | 8 cards no recorte com plano de acao definido |
| Comunicacao | 70 | atencao | comentarios existem, mas nao fecham todas as decisoes |
| Documentacao | 58 | critico | descricoes incompletas limitam rastreabilidade |
| Risco | 64 | atencao | 2 riscos prioritarios identificados |
| Execucao | 73 | bom | acoes recomendadas possuem dono e prazo |
| Maturidade | 75 | bom | quality gate e baseline ativos |

## Benchmark Interno

SLA, ownership e documentacao pioraram no periodo; comunicacao ficou estavel.
**Confiança:** 0.78

| Métrica | Atual | Anterior | Últimos 90 dias | Tendência |
| --- | ---: | ---: | ---: | --- |
| SLA compliance | 50% | 62% | 68% | piorou |
| Cards vencidos | 4 | 3 | 2,4 media | piorou |
| Cards sem responsavel | 3 | 2 | 1,8 media | piorou |
| Comentarios conclusivos | 3 | 3 | sem dados suficientes | estavel |

### Top 3 Drivers

- **Cards vencidos concentram risco operacional:** Replanejar cards vencidos hoje. Evidências: 4 de 8 cards estao abertos e vencidos.
- **Descricoes incompletas limitam decisao:** Exigir descricao minima. Evidências: 5 descricoes incompletas.
- **Cards sem responsavel reduzem accountability:** Atribuir responsaveis. Evidências: 3 cards sem responsavel.

### Decisões Prioritárias

- **Repriorizar cards vencidos.:** A exposicao operacional continua crescendo. Evidências: 4 cards vencidos.
- **Atribuir responsaveis para cards sem dono.:** Cards criticos podem continuar sem acompanhamento ate o proximo ciclo. Evidências: 3 cards sem responsavel.
- **Exigir descricao minima.:** Decisoes continuam dependendo de suposicao. Evidências: 5 descricoes incompletas.

### Plano de Ação

- **Replanejar cards vencidos.:** Reduzir risco de SLA. Evidências: 4 cards vencidos.
- **Atribuir responsaveis para cards sem dono.:** Melhorar accountability. Evidências: 3 cards sem responsavel.
- **Aplicar checklist minimo nas novas demandas.:** Reduzir retrabalho de triagem. Evidências: 5 descricoes incompletas.

## Narrativa Executiva


## O que merece atenção

- **Concentracao elevada de cards vencidos:** Evidências: 4 de 8 cards vencidos. Confiança: 0.9.

## Descobertas

- **50% dos cards analisados concentram o principal risco de SLA.:** Evidências: 4 de 8 cards vencidos. Confiança: 0.86.

## Anomalias

- Nenhum item com evidencia suficiente no recorte analisado.

## Hotspots

```json
{
  "categorias": [
    {
      "name": "Incidentes",
      "count": 4
    }
  ],
  "gargalos": [
    {
      "name": "Cards vencidos sem replanejamento",
      "count": 4
    }
  ]
}
```

## Oportunidades

- **Padronizar tratamento de incidentes vencidos:** Evidências: 4 cards vencidos; categoria incidente recorrente. Confiança: 0.84.
- **Melhorar qualidade das descricoes:** Evidências: 5 descricoes incompletas. Confiança: 0.82.

## Cenário provável

- **Risco crescente de rompimento de SLA.:** Base: 4 cards vencidos. Confiança: 0.76.

## Indicadores Analíticos

- SLA: {"overdue_open_cards": 4, "cards_without_due_date": 2, "cards_due_in_48h": 1, "compliance_pct": 50}
- Qualidade: {"missing_owner_count": 3, "incomplete_description_count": 5, "cards_with_pending_checklists": 4}
- Comunicação: {"total_comments": 9, "cards_without_comments": 2}

## Recomendações

- **alta:** Replanejar cards vencidos. Evidências: 4 cards vencidos

## Resumo

```json
{
  "report_type": "EXECUTIVO"
}
```