# Discovery Insights Engine 2.0

## Objetivo

O Discovery Insights Engine adiciona descoberta automatica aos relatorios do EOR. Ele nao depende de filtros especificos e procura sinais que o usuario talvez nao tenha perguntado:

- padroes;
- anomalias;
- concentracoes;
- recorrencias;
- desvios;
- mudancas de comportamento;
- correlacoes;
- oportunidades.

## Localizacao

Implementacao principal:

```text
apps/intelligence/services/report_query/engine/discovery_engine.py
```

Integracao:

```text
apps/intelligence/services/report_query/engine/executor.py
apps/intelligence/services/report_query/exporters/formats.py
```

## Entrada

O motor consome apenas dados ja calculados:

- `analytical.metrics_pack`
- `analytical.activity_classification.cards`
- `analytical.recommendations`
- `executive_narrative.executive_readability_score`

Nao usa IA externa e nao inventa fatos.

## Saida

O resultado do relatorio passa a incluir:

```json
{
  "discovery": {
    "anomalies": [],
    "patterns": [],
    "correlations": [],
    "hotspots": {},
    "opportunities": [],
    "executive_highlights": [],
    "executive_surprises": [],
    "what_happens_next": [],
    "report_intelligence_score": {}
  }
}
```

## Anomaly Detector

Detecta anomalias com threshold e evidencia:

- cards vencidos;
- cards sem prazo;
- cards sem responsavel;
- descricoes incompletas;
- cards sem comentarios;
- cards parados ha 7 dias ou mais;
- membro sobrecarregado;
- categoria critica por risco.

Cada anomalia contem:

- `title`
- `kind`
- `severity`
- `metric_source`
- `evidence`
- `impact`
- `confidence`

## Pattern Discovery

Descobre automaticamente:

- concentracao por tipo de atividade;
- concentracao por etiqueta;
- concentracao por lista;
- concentracao por status;
- crescimento ou queda semanal quando ha tendencia observada;
- sistemas ou projetos citados de forma recorrente em titulos.

## Correlation Engine

Correlacoes usam coeficiente Phi em variaveis binarias.

Amostra minima:

```text
MIN_CORRELATION_SAMPLE = 4
```

Correlacoes atuais:

- descricao pobre x alto risco;
- sem comentarios x parado ha 7 dias;
- checklist pendente x alto risco;
- sem comentarios x alto risco.

Cada correlacao retorna:

- coeficiente;
- amostra;
- confianca;
- evidencias;
- limitacoes.

## Hotspots

Mapa de maiores problemas:

- top categorias;
- top membros;
- top sistemas;
- top projetos;
- top tipos;
- top riscos;
- top gargalos.

## Opportunity Detector

Detecta oportunidades como:

- categorias candidatas a playbook;
- automacao de qualidade de descricao;
- follow-up para cards sem interacao;
- possiveis duplicidades;
- intervencao orientada por correlacao.

## Executive Highlights

Bloco `executive_highlights` responde "O que merece atencao".

Regras:

- maximo de 10 itens;
- ordenacao por impacto, severidade e confianca;
- cada item possui evidencia.

## Executive Surprises

Bloco `executive_surprises` gera descobertas textuais apenas quando ha suporte estatistico simples.

Exemplos:

- concentracao de 60% ou mais dos cards em duas categorias;
- concentracao de 60% ou mais dos comentarios em poucos cards.

## What Happens Next

Bloco `what_happens_next` gera cenario provavel apenas quando existe tendencia observada ou anomalia de SLA com base explicita.

Cada item contem:

- `scenario`
- `confidence`
- `basis`
- `trend_observed`

## Report Intelligence Score

Escala: 0 a 100.

Componentes:

- insights;
- correlacoes;
- anomalias;
- descobertas;
- tendencias;
- recomendacoes;
- cobertura;
- explicabilidade.

## Exports

JSON inclui `discovery` completo.

Markdown inclui:

- O que merece atencao;
- Descobertas;
- Anomalias;
- Hotspots;
- Oportunidades;
- Cenario provavel.

PDF inclui linhas executivas resumidas de atencao, descoberta e cenario.

PPTX outline inclui `report_intelligence`, `discovery` e slide de descobertas.

## Guardrails

- Nenhuma descoberta sem evidencia.
- Nenhuma correlacao sem amostra minima.
- Nenhuma previsao sem base observada.
- Nenhuma anomalia e emitida para board pequeno e limpo sem threshold atingido.
- Toda correlacao declara limitacoes.
