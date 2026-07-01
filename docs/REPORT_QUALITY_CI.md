# Report Quality CI

## Objetivo

Impedir regressao da qualidade analitica, narrativa e decisoria dos relatorios.

## Baseline versionado

Arquivo:

```text
docs/report_quality_baseline.json
```

Contem:

- DecisionValueScore minimo;
- ReportQualityScore minimo;
- ReportIntelligenceScore minimo;
- ExecutiveStoryQualityScore minimo;
- secoes obrigatorias;
- exports obrigatorios;
- data da baseline;
- modelo EOR.

## Comando minimo de CI

```powershell
$env:EOR_TESTING='true'; python manage.py validate_report_quality --fixture --compare-baseline --json
```

Esse comando:

- nao depende de PostgreSQL;
- usa fixture realista;
- valida o contrato executivo do relatorio;
- compara contra `docs/report_quality_baseline.json`;
- falha se houver regressao.

## Tolerancia

Para permitir pequena oscilacao controlada:

```powershell
$env:EOR_TESTING='true'; python manage.py validate_report_quality --fixture --compare-baseline --tolerance 5 --json
```

A tolerancia reduz temporariamente o minimo exigido por score. Exemplo: baseline 90 com tolerancia 5 aceita 85.

## Salvar nova baseline

Use apenas quando a mudanca de qualidade for intencional e revisada:

```powershell
$env:EOR_TESTING='true'; python manage.py validate_report_quality --fixture --save-baseline --json
```

Para arquivo customizado:

```powershell
$env:EOR_TESTING='true'; python manage.py validate_report_quality --fixture --save-baseline --baseline-file docs/report_quality_baseline.json --json
```

## Caminho staging com banco real

```powershell
python manage.py validate_report_quality --board-id <id> --period LAST_30_DAYS --compare-baseline --json
```

Saida esperada:

- `PASS`, `WARNING` ou `FAIL`;
- scores atuais;
- diferencas contra baseline;
- secoes ausentes;
- exports ausentes;
- checks obrigatorios quebrados;
- regressoes detectadas.

## Falha de baseline ausente

Se o arquivo nao existir, o comando retorna `FAIL` com:

```text
Baseline file not found: <path>
```

## Politica

Uma mudanca em relatorios so deve ser aceita se:

- o fixture passar contra baseline;
- o modo staging passar contra baseline quando houver banco real;
- nenhuma regressao critica for ignorada sem justificativa documentada.
