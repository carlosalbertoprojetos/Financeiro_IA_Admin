# Tenant Isolation Audit

## Objetivo

Remover o bloqueio principal para SaaS multi-tenant: impedir que dados de um cliente sejam retornados para outro.

## Modelos auditados

### Core

- `Tenant` recriado em `core.models`.
- Campos: `name`, `slug`, `plan`, `is_active`.

### Integrations

- `IntegrationConnection` agora possui `tenant`.
- `CanonicalTaskRecord` herda escopo por `connection`.
- `IntegrationState` herda escopo por `connection`.
- `IngestionQueueEvent` ainda usa `connection_id` textual; deve ser reforcado em fase posterior.

### Legacy Trello

- `Board` agora possui `tenant`.
- `Card`, `Action`, `BoardList`, `Snapshot` e historicos herdam escopo por `Board`.

### Intelligence

- Registros com `board_id` textual continuam exigindo cuidado.
- APIs novas de product readiness usam `X-Tenant-Id` e restringem dados via boards do tenant.

## Componentes implementados

- `core/tenant_context.py`
- `core/tenant_queryset.py`
- `core/middleware.py`
- `TenantScopedQuerySet`
- `TenantScopedManager`
- `TenantContextMiddleware`
- `get_request_tenant`
- `assert_board_belongs_to_tenant`

## Bloqueios aplicados

Rotas pagas sensiveis agora exigem tenant:

- `GET /api/system/usage/`
- `GET /api/system/customer-success/`
- `GET /api/system/marketplace/`
- `GET /api/system/onboarding/state/`
- `POST /api/system/onboarding/select-boards/`
- `POST /api/system/onboarding/sync/`
- `POST /api/system/onboarding/generate-first-report/`

## Testes adicionados

Arquivo:

```text
apps/intelligence/tests/product_readiness/test_product_readiness.py
```

Cobre:

- rota paga sem tenant retorna 403;
- tenant A nao seleciona board do tenant B;
- analytics usa tenant scope;
- Starter nao acessa marketplace;
- Enterprise acessa marketplace.

## Riscos remanescentes

- Endpoints legados de inteligencia ainda aceitam `board_id` diretamente.
- Cache global precisa padronizar chave `tenant_id:board_id`.
- Registros antigos precisam backfill de `tenant_id`.
- `IngestionQueueEvent.connection_id` ainda e textual.

## Status

O bloqueio critico foi reduzido para **WARNING** no release gate focado. Para `READY`, completar backfill e migrar endpoints legados para `assert_board_belongs_to_tenant`.

