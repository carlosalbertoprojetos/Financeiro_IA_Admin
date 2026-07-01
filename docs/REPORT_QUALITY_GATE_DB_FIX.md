# Report Quality Gate DB Fix

## Objetivo

Garantir que o comando abaixo consiga validar relatórios sem depender de um PostgreSQL local indisponível:

```powershell
python manage.py validate_report_quality --json
```

Agora existem dois modos:

- modo `database`: valida board real usando banco;
- modo `fixture`: valida payload realista em memória, sem banco.

## Diagnóstico do bloqueio

Falha observada no modo real:

```text
connection timeout expired
host: localhost
port: 5433
database: tip_backend
```

Origem:

- backend configurado como PostgreSQL;
- host/porta definidos por variáveis `POSTGRES_*`;
- ambiente atual aponta `POSTGRES_HOST=localhost`;
- ambiente atual aponta `POSTGRES_PORT=5433`;
- `POSTGRES_DB=tip_backend`;
- `POSTGRES_CONNECT_TIMEOUT=5`;
- `EOR_TESTING` vazio no modo real;
- PostgreSQL local não responde em `localhost:5433`.

Consequência:

- o comando não consegue selecionar board real;
- nenhuma validação produtiva pode ocorrer enquanto o banco estiver fora;
- antes do fix, o usuário recebia stack trace;
- depois do fix, o comando retorna `FAIL` controlado com diagnóstico e instruções.

## Modo fixture

Novo comando:

```powershell
python manage.py validate_report_quality --fixture --json
```

Em CI/local rápido:

```powershell
$env:EOR_TESTING='true'; python manage.py validate_report_quality --fixture --json
```

Esse modo:

- não consulta banco;
- não cria dados no ORM;
- usa payload realista de relatório executivo;
- valida `DecisionValueScore`;
- valida `executive_story`;
- valida `discovery`;
- valida exports JSON, Markdown, PDF e PPTX;
- retorna `PASS`, `WARNING` ou `FAIL`.

## Fixture variants

Fixture completa:

```powershell
python manage.py validate_report_quality --fixture --json
```

Fixture negativa para testar gate:

```powershell
python manage.py validate_report_quality --fixture --fixture-variant missing_story --json
```

Esperado:

- `complete`: `PASS`;
- `missing_story`: `FAIL`.

## Modo database

Com board explícito:

```powershell
python manage.py validate_report_quality --board-id <BOARD_ID> --json
```

Com período:

```powershell
python manage.py validate_report_quality --board-id <BOARD_ID> --period last_30_days --json
```

Sem `--board-id`, o comando tenta selecionar o primeiro board local.

## Erro amigável

Quando o banco está indisponível, o comando retorna:

```json
{
  "status": "FAIL",
  "mode": "database",
  "decision_value_score": 0,
  "classification": "fraco",
  "failures": ["database unavailable: ..."],
  "database": {
    "engine": "django.db.backends.postgresql",
    "host": "localhost",
    "port": "5433",
    "database": "tip_backend",
    "connect_timeout": 5,
    "EOR_TESTING": ""
  },
  "instructions": []
}
```

## Instruções de correção do banco

1. Subir o PostgreSQL/container configurado para o EOR.
2. Confirmar `POSTGRES_HOST`.
3. Confirmar `POSTGRES_PORT`.
4. Confirmar `POSTGRES_DB`.
5. Confirmar `POSTGRES_USER`.
6. Ajustar `POSTGRES_CONNECT_TIMEOUT` se necessário.
7. Rodar novamente com `--board-id`.

## Pipeline de CI

Use fixture mode para validação rápida e determinística:

```powershell
$env:EOR_TESTING='true'; python manage.py validate_report_quality --fixture --json
```

Critérios:

- não depende de PostgreSQL;
- não depende de board real;
- valida o gate completo;
- falha se o contrato executivo quebrar.

## Arquivos alterados

- `apps/intelligence/management/commands/validate_report_quality.py`
- `apps/intelligence/services/report_query/quality/fixtures.py`
- `apps/intelligence/services/report_query/quality/validator.py`
- `apps/intelligence/tests/test_report_quality_validator.py`

## Testes automatizados

Cenários cobertos:

- fixture mode `PASS`;
- fixture mode `FAIL` quando `executive_story` está ausente;
- database unavailable retorna `FAIL` controlado;
- saída JSON válida;
- score mínimo respeitado.
