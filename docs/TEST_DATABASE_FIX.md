# Test Database Fix

## Problema

A suíte focada travava ou falhava durante:

```text
Creating test database for alias 'default'...
```

Havia dois fatores:

1. O PostgreSQL local configurado em `.env` apontava para `localhost:5433` e nao estava respondendo de forma confiavel.
2. A migration `core.0002_remove_tenantmembership_tenant_and_more` removia campos de `TenantMembership` antes de remover a constraint `unique_user_tenant_membership`, quebrando a montagem do banco SQLite de teste.

## Solucao aplicada

### Timeout de PostgreSQL

`tip_backend/settings/base.py` passou a usar:

```text
POSTGRES_CONNECT_TIMEOUT=5
```

Isso evita travamento silencioso quando o banco produtivo/local esta indisponivel.

### Banco de teste local

Foi adicionado modo explicito:

```powershell
$env:EOR_TESTING='true'
```

Quando ativo, o Django usa SQLite local real para testes focados:

```text
test_eor.sqlite3
```

O arquivo foi adicionado ao `.gitignore`.

### Migration corrigida

`core/migrations/0002_remove_tenantmembership_tenant_and_more.py` agora remove a constraint antes de remover os campos.

## Evidencia

Comando executado:

```powershell
$env:EOR_TESTING='true'; python manage.py test apps.intelligence.tests.product_readiness
```

Resultado:

```text
Found 13 test(s).
Creating test database for alias 'default'...
Ran 13 tests in 0.176s
OK
Destroying test database for alias 'default'...
```

## Limites

- PostgreSQL continua sendo o banco normal do EOR.
- O modo SQLite e apenas para suite focada local e release gate tecnico.
- Para homologacao final, rodar a mesma suite com PostgreSQL ativo e migrations aplicadas.

