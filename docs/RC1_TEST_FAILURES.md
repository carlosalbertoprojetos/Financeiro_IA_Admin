# RC1 Test Failures

Data: 2026-06-27

## Execucao Inicial

Comando:

```powershell
$env:EOR_TESTING='true'; python manage.py test
```

Resultado inicial:

- testes encontrados: 469;
- failures: 2;
- errors: 13;
- status: FAIL.

## Errors

### Infrastructure

| Arquivo | Erro | Causa | Impacto | Prioridade |
| --- | --- | --- | --- | --- |
| `apps/dashboards/services/canonical_metrics.py` | `django.db.utils.NotSupportedError: contains lookup is not supported on this database backend` | `_overdue_tasks()` usava `metadata__contains={"closed": True}` em `JSONField`; SQLite de teste nao suporta esse lookup. | Quebrava dashboards, analytics, reports canonicos e testes de scope. | P0 |
| `apps/intelligence/services/pilot/report_generator.py` | `django.db.utils.NotSupportedError: contains lookup is not supported on this database backend` | `generate_executive_daily_report()` usava `original_action_json__contains={"execution_mode": "SEMI_AUTOMATIC"}`. | Quebrava relatorio diario do piloto no ambiente de teste local/CI. | P0 |

Testes afetados pelo mesmo erro:

- `apps.dashboards.tests.test_scope.CanonicalScopeTests`
- `apps.dashboards.tests.test_canonical_analytics`
- `apps.reports` via endpoints canonicos
- `apps.intelligence.tests.pilot.test_pocl.ReportGeneratorTests.test_generate_daily_report`

## Fail

### Workers

| Arquivo | Erro | Causa | Impacto | Prioridade |
| --- | --- | --- | --- | --- |
| `apps/integrations/tests/test_trello_worker.py` | `analytics_refreshed: 0 != 1` | Efeito colateral do erro de infrastructure: o worker chamava refresh de analytics, que falhava no lookup JSON antes de incrementar `analytics_refreshed`. | Ingestion completed nao comprovava refresh de cache no teste. | P0 |

### Description Intelligence

| Arquivo | Erro | Causa | Impacto | Prioridade |
| --- | --- | --- | --- | --- |
| `apps/intelligence/tests/test_description_intelligence.py` | `ANALYSIS_PERFORMED` ausente | Regex reconhecia `analisado/analisada`, mas nao o substantivo `Análise realizada`. | Descricoes operacionais com analise registrada nao eram classificadas como evento de analise. | P0 |

## Grupos Sem Falhas RC1

- Timeline: sem falha especifica apos correcoes.
- Trello: worker passou apos correcao de infraestrutura.
- Exports: sem falha na suite final.
- DAL: sem falha na suite final.
- OLE: sem falha na suite final.
- BVE: sem falha na suite final.
- Report Engine: passou na suite final e no quality gate.

## Execucao Final

Comando:

```powershell
$env:EOR_TESTING='true'; python manage.py test
```

Resultado final:

- testes encontrados: 469;
- failures: 0;
- errors: 0;
- status: PASS.
