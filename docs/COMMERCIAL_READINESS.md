# Commercial Readiness

## Pergunta central

O EOR esta pronto para venda?

Resposta curta: **nao para venda SaaS multi-tenant plena ainda**. O sistema tem uma base tecnica forte e agora possui uma camada explicita de prontidao comercial, mas ainda existem gaps criticos em isolamento de tenant, enforcement de planos, operacao de workers e validacao produtiva com clientes reais.

## O que foi entregue nesta fase

### Workspace Validation

- `GET /api/system/workspace/`
- `python manage.py validate_eor_workspace`
- Documento: `docs/WORKSPACE_VALIDATION.md`

### Health Check

Endpoint:

```text
GET /api/system/health/
```

Verifica:

- banco;
- cache;
- filas;
- workers;
- Trello configurado;
- IA configurada;
- storage basico.

Nenhuma chamada externa real e feita por padrao.

O banco usa timeout configuravel para evitar health check travado:

```text
POSTGRES_CONNECT_TIMEOUT=5
```

### Self Diagnostics

Endpoint:

```text
GET /api/system/diagnostics/
```

Detecta:

- credenciais Trello ausentes;
- conexoes sem sync recente;
- boards sem cards;
- eventos pendentes na fila;
- falha de cache.

Cada finding retorna evidencia e recomendacao.

### Usage Analytics

Endpoint:

```text
GET /api/system/usage/
```

Metricas:

- boards sincronizados;
- cards analisados;
- eventos processados;
- relatorios gerados;
- acoes sugeridas;
- acoes aceitas;
- ROI gerado via registros BVE.

### Customer Success Dashboard

Endpoint:

```text
GET /api/system/customer-success/
```

Mostra valor gerado, problemas encontrados, melhorias sugeridas, maturidade operacional e ROI a partir de registros persistidos.

### Licensing

Endpoint:

```text
GET /api/system/licensing/
```

Planos definidos:

- Starter
- Professional
- Business
- Enterprise

Status: catalogo explicito criado; enforcement por tenant ainda precisa ser conectado antes de venda paga.

### Connector Framework

Endpoint:

```text
GET /api/system/connectors/
```

Conectores catalogados:

- Trello
- Jira
- ClickUp
- Monday
- Asana
- Azure DevOps
- GitHub Projects
- Planner
- Notion

Status:

- Trello: disponivel.
- Demais: registrados como placeholders explicitos, sem suporte produtivo declarado.

### Operational Marketplace

Endpoint:

```text
GET /api/system/marketplace/
```

Categorias preparadas:

- KPIs;
- dashboards;
- conectores;
- exporters;
- regras;
- playbooks.

Guardrail principal: plugins nao podem burlar tenant scope nem aprovacao humana do DAL.

### Executive Demo Mode

Endpoint:

```text
GET /api/system/demo/
```

Fornece payload demonstrativo sem token real, sem chamada externa e sem misturar metrica demo com dados de cliente.

### Customer Onboarding

Endpoint:

```text
GET /api/system/onboarding/
```

Fluxo definido:

1. Cadastro
2. Organizacao
3. Token Trello
4. Teste de conexao
5. Sincronizacao inicial
6. Descoberta automatica de boards
7. Escolha dos boards
8. Indexacao
9. Primeira analise
10. Primeiro relatorio executivo

Meta: Time To First Value menor que 10 minutos.

## Multi-tenant hardening

Endpoint:

```text
GET /api/system/multi-tenant/
```

Resultado atual: **bloqueado para SaaS pago multi-tenant**.

Gaps principais:

- modelos legados Trello (`Board`, `Card`, `Action`) nao possuem tenant obrigatorio;
- varias APIs aceitam `board_id` diretamente;
- cache precisa de prefixo tenant-aware por feature;
- exports e logs precisam enforcement por tenant antes de uso comercial.

Recomendacao:

1. Criar entidade `Tenant`/`Account` canonica.
2. Vincular conexoes, boards, cards, acoes, relatorios, decisoes e valor financeiro ao tenant.
3. Adicionar middleware/resolver de tenant.
4. Exigir filtros tenant-aware em todos os querysets.
5. Criar testes negativos de vazamento entre tenants.

## Riscos que impedem producao comercial

- Isolamento multi-tenant ainda nao e total.
- Planos existem como catalogo, mas ainda nao bloqueiam features em runtime.
- Onboarding esta definido, mas ainda precisa UI guiada e persistencia de progresso.
- Health check nao verifica Trello/OpenAI com probe externo por padrao.
- Conectores alem de Trello sao placeholders.
- Workers/filas precisam validacao em ambiente real.
- ROI real depende de registros BVE/decisoes reais; nao deve ser simulado.

## Roadmap para versao 1.0

### Marco 1: SaaS Safety

- Tenant model canonico.
- Tenant-scoped querysets.
- Tenant-aware cache keys.
- Auditoria de exports/logs por tenant.
- Testes de isolamento.

### Marco 2: Onboarding operacional

- UI de onboarding.
- Estado persistido por organizacao.
- Descoberta real de boards.
- Primeiro sync com progresso.
- Primeiro relatorio automatico.

### Marco 3: Comercializacao

- Billing/licensing enforcement.
- Demo mode visual.
- Customer Success Dashboard no frontend.
- Health page operacional.
- Runbook de suporte.

### Marco 4: Expansao

- Jira e ClickUp produtivos.
- Marketplace registry persistente.
- Plugin signing/policy.
- Enterprise SSO/auditoria avancada.

## Definicao de pronto para venda

O EOR fica pronto para venda SaaS quando:

- nenhum dado operacional pode cruzar tenant;
- planos bloqueiam recursos em runtime;
- onboarding gera primeiro relatorio em menos de 10 minutos;
- health e diagnostics operam em producao;
- demo mode permite apresentacao sem credencial real;
- pelo menos um cliente piloto confirma valor observado, nao inferido.
