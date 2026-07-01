# How To Generate Executive Report Sample

## Gerar amostra fixture

```powershell
$env:EOR_TESTING='true'; python manage.py validate_report_quality --fixture --compare-baseline --json
```

A amostra fixture pode ser gerada a partir de `build_quality_gate_fixture()` e salva em `docs/samples/reports/` nos formatos JSON, Markdown, PDF e PPTX.

A versao 1.0 da amostra deve conter:

- Executive Brief;
- 5 KPIs executivos;
- Scorecard Executivo;
- Benchmark Interno;
- Top 3 Drivers;
- 3 decisoes prioritarias;
- riscos e oportunidades;
- plano de acao com dono, prazo, evidencia e metrica de sucesso.

## Gerar amostra com board real

```powershell
python manage.py validate_report_quality --board-id <BOARD_ID> --period LAST_30_DAYS --compare-baseline --json
```

Se o banco estiver indispon?vel, o comando retorna `FAIL` controlado com host, porta, database e instru??es.

## Validar qualidade

```powershell
$env:EOR_TESTING='true'; python manage.py validate_report_quality --fixture --compare-baseline --json
```

## Comparar baseline

```powershell
$env:EOR_TESTING='true'; python manage.py validate_report_quality --fixture --compare-baseline --tolerance 5 --json
```

## Arquivos esperados

```text
docs/samples/reports/executive_report_sample.json
docs/samples/reports/executive_report_sample.md
docs/samples/reports/executive_report_sample.pdf
docs/samples/reports/executive_report_sample.pptx
docs/samples/reports/REPORT_SAMPLE_REVIEW.md
```

## Observa??o

A amostra fixture ? indicada para revis?o de produto/comercial sem depend?ncia de PostgreSQL. Para valida??o comercial com dados reais, use o modo `--board-id` em staging.

## Revisao comercial

Arquivos de apoio:

```text
docs/samples/reports/EXECUTIVE_REVIEW_FEEDBACK.md
docs/samples/reports/REPORT_PRODUCT_BACKLOG.md
docs/PRODUCT_READINESS_SCORE.md
docs/FINAL_RELEASE_VALIDATION.md
```

Antes de demo externa, confirmar que `sample_validation.json` esta com `status: PASS` e que o PPTX abre com os slides `Executive Brief`, `Historia Executiva`, `Scorecard Executivo`, `Benchmark Interno` e `Top 3 Drivers`.
