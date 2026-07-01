# Workspace Validation

## Objetivo

Garantir que tarefas de hardening comercial sejam executadas somente no workspace correto do EOR.

O workspace esperado e:

```text
Executive Operational Report / Intelligence Platform
```

## Mecanismo implementado

Servico:

```text
apps/intelligence/services/product_readiness/workspace.py
```

Endpoint:

```text
GET /api/system/workspace/
```

Comando:

```powershell
python manage.py validate_eor_workspace
python manage.py validate_eor_workspace --json
```

## Itens validados

Arquivos obrigatorios:

- `manage.py`
- `README.md`
- `requirements.txt`
- `docker-compose.yml`
- `Executar_EOR.bat`

Diretorios obrigatorios:

- `ai`
- `analytics`
- `apps`
- `core`
- `dashboard`
- `frontend`
- `integrations`
- `reports`
- `tip_backend`

Apps obrigatorios:

- `apps.integrations`
- `apps.intelligence`
- `apps.settings`
- `integrations.trello`
- `rest_framework`

Modulos EOR obrigatorios:

- `semantic_layer`
- `timeline`
- `risk_engine`
- `decision_layer`
- `organizational_learning`
- `business_value`
- `pilot`

Versao de modelo:

```text
CURRENT_MODEL_VERSION = 1.1
```

## Comportamento esperado

Quando o workspace esta correto:

```json
{
  "workspace": "EOR",
  "status": "ready",
  "model_version": "1.1"
}
```

Quando algum arquivo, app ou modulo obrigatorio esta ausente:

```json
{
  "workspace": "EOR",
  "status": "blocked"
}
```

O comando de terminal falha com `CommandError` quando o workspace nao esta pronto.

## Politica operacional

Antes de qualquer sprint de produto:

1. Rodar `python manage.py validate_eor_workspace`.
2. Se o status for `blocked`, nao implementar alteracoes.
3. Corrigir o workspace ou abrir o repositorio correto.
4. Repetir a validacao.

## Limitacoes

- A validacao confirma estrutura e modulos do EOR, nao garante que banco, Redis ou Trello estejam disponiveis.
- Health operacional fica em `GET /api/system/health/`.
- Readiness comercial fica documentado em `docs/COMMERCIAL_READINESS.md`.

