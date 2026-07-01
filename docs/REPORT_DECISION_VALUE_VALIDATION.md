# Report Decision Value Validation

## Objetivo

Validar se os relatorios enriquecidos do EOR melhoraram para tomada de decisao executiva. A validacao mede clareza, utilidade, completude, rastreabilidade, priorizacao e capacidade de orientar decisao.

## Workspace

Comando obrigatorio executado antes das alteracoes:

```powershell
python manage.py validate_eor_workspace --json
```

Resultado:

- workspace: `EOR`
- status: `ready`
- model_version: `1.1`
- checks: 27
- failures: 0
- warnings: 0

## Validador criado

Modulo:

```text
apps/intelligence/services/report_query/quality/validator.py
```

Comando:

```powershell
python manage.py validate_report_quality --board-id <BOARD_ID>
python manage.py validate_report_quality --board-id <BOARD_ID> --json
```

## DecisionValueScore

Escala: 0 a 100.

Classificacao:

- 0-39: fraco
- 40-59: aceitavel
- 60-79: bom
- 80-100: executivo

Criterios:

- clareza executiva;
- capacidade de decisao;
- evidencia;
- priorizacao;
- profundidade analitica;
- recomendacoes acionaveis;
- previsao/cenario provavel;
- qualidade dos exports.

## Quality Gate

Retornos possiveis:

- `PASS`
- `WARNING`
- `FAIL`

Falha se:

- `DecisionValueScore < 70`;
- `executive_story` ausente;
- decisoes sem evidencia;
- relatorio sem recomendacoes acionaveis;
- exports sem blocos executivos.

## Checks objetivos

O validador verifica:

- `executive_story` presente;
- Top 3 drivers presentes;
- decisoes com evidencia;
- recomendacoes acionaveis;
- riscos priorizados;
- metricas analiticas presentes;
- discovery presente;
- descricao considerada;
- ausencia de secoes criticas vazias;
- exports carregam narrativa;
- cenario provavel presente;
- evidence map rastreavel.

## Comparacao por estagio

O validador gera `stage_comparison` para:

1. `base`
2. `analytical_enrichment`
3. `executive_narrative`
4. `discovery`
5. `executive_story`

Metricas comparadas:

- numero de metricas;
- numero de evidencias;
- numero de decisoes;
- numero de recomendacoes acionaveis;
- DecisionValueScore;
- ReportQualityScore;
- ReportIntelligenceScore;
- ExecutiveStoryQualityScore.

## Evidencia de superioridade

O relatorio atual e considerado superior ao relatorio base quando:

- aumenta evidencias rastreaveis;
- adiciona decisoes com evidencia;
- reduz secoes criticas vazias;
- inclui priorizacao por drivers;
- inclui plano de acao;
- melhora `DecisionValueScore`;
- carrega a historia nos exports executivos.

## Validacao automatizada

Teste criado:

```text
apps/intelligence/tests/test_report_quality_validator.py
```

Cenarios cobertos:

- calculo do DecisionValueScore;
- falha quando falta evidencia;
- falha quando falta executive_story;
- sucesso com relatorio executivo completo;
- validacao de exports;
- comando `validate_report_quality`.

## Comandos executados

```powershell
$env:EOR_TESTING='true'; python manage.py test apps.intelligence.tests.test_report_quality_validator
python -m compileall apps\intelligence\services\report_query\quality\validator.py apps\intelligence\management\commands\validate_report_quality.py apps\intelligence\tests\test_report_quality_validator.py
```

## Execucao no ambiente atual

O comando tambem foi executado contra o ambiente real:

```powershell
python manage.py validate_report_quality --json
```

Resultado observado:

- status: `FAIL`
- causa: banco PostgreSQL indisponivel em `localhost:5433`
- impacto: nao foi possivel selecionar o board real local para medir o relatorio produtivo nesta execucao.

O comando foi ajustado para retornar falha controlada e motivo objetivo quando o banco estiver indisponivel, em vez de stack trace.

## Limitacoes

- PDF e validado por presenca, tipo e tamanho porque o conteudo e binario.
- A comparacao por estagio usa o payload do relatorio atual para reconstruir camadas incrementais.
- A validacao de board real depende de haver dados locais sincronizados no ambiente.
