# Plan Enforcement

## Objetivo

Transformar o catalogo Starter/Professional/Business/Enterprise em controle runtime.

## Implementacao

Servico:

```text
apps/intelligence/services/product_readiness/licensing.py
```

Funcoes:

- `plan_catalog()`
- `is_feature_enabled(plan_name, feature)`
- `plan_for_tenant(tenant)`
- `check_plan_limits(tenant, boards, cards_analyzed, connector)`
- `require_plan_feature(tenant, feature)`

## Planos

### Starter

- 2 boards
- 5 usuarios
- 1.000 cards analisados
- Trello
- sem exports
- sem marketplace

### Professional

- 10 boards
- 25 usuarios
- 10.000 cards analisados
- Trello, Jira, ClickUp
- exports liberados

### Business

- 50 boards
- 100 usuarios
- 100.000 cards analisados
- DAL/OLE/BVE/customer success
- marketplace liberado

### Enterprise

- limites ilimitados
- todos os conectores
- marketplace
- auditoria avancada

## Bloqueios runtime implementados

- `GET /api/system/marketplace/` exige feature `marketplace`.
- `POST /api/system/onboarding/select-boards/` aplica limite de boards do plano.
- Mensagens de upgrade usam `PermissionDenied` ou `402 Payment Required` com detalhe do limite.

## Testes

Comando:

```powershell
$env:EOR_TESTING='true'; python manage.py test apps.intelligence.tests.product_readiness
```

Cenarios:

- Starter bloqueia marketplace com 403.
- Enterprise libera marketplace com 200.
- Starter bloqueia selecao acima de 2 boards com 402.

## Proximos pontos de enforcement

- Exports legados.
- DAL/OLE/BVE em endpoints diretos.
- Limite de cards analisados por periodo.
- Conectores por plano no momento de criar `IntegrationConnection`.
