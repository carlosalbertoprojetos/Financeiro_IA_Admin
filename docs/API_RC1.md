# API RC1

Data: 2026-06-27

## Superficies Validadas

- `/api/v1/reports/`
- `/api/v1/reports/executive/`
- `/api/reports/query/`
- `/api/v1/dashboards/metrics/`
- `/api/v1/dashboards/analytics/`
- `/api/system/*`

## Gates

```powershell
python manage.py validate_eor_workspace --json
$env:EOR_TESTING='true'; python manage.py validate_report_quality --fixture --compare-baseline --json
$env:EOR_TESTING='true'; python manage.py test
```

## Observacao

RC1 valida APIs em ambiente local/teste. Probes externos de Trello, Redis e PostgreSQL staging devem ser executados antes de piloto real.
