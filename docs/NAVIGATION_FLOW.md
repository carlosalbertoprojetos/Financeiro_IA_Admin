# EOP/TIP - Fluxo de Navegacao e Jornada do Usuario

## 1. Estrutura atual encontrada

### Navegacao visivel no frontend

O frontend autenticado possui hoje 5 entradas principais:

| Rota | Tela | Tipo | Papel na jornada |
| --- | --- | --- | --- |
| `/dashboard` | Dashboard Operacional | Analitica/operacional | Primeira leitura do estado do board sincronizado |
| `/integrations` | Integracoes | Configuracao operacional | Conectar Trello e executar sincronizacao |
| `/reports` | Relatorios | Analitica/relatorios | Gerar e baixar relatorio executivo em PDF |
| `/analytics` | Analises | Analitica | Ver metricas e insights derivados das tasks |
| `/settings` | Configuracoes | Configuracao/administrativa | Workspace, Trello, OpenAI e area admin |

### Superficie de API e modulos registrados

| Prefixo | Funcionalidades | Classificacao |
| --- | --- | --- |
| `/api/v1/integrations/`, `/api/v1/data-sources/` | Conexao Trello, status, sync, placeholders Excel/Jira/ClickUp | Operacional/configuracao |
| `/api/v1/dashboards/`, `/api/dashboard/` | Overview, metricas, analytics canonico, produtividade, eficiencia, gargalos | Analitica |
| `/api/v1/analytics/`, `/api/analytics/` | Metricas gerais, time, cards e gaps | Analitica |
| `/api/v1/reports/`, `/api/reports/` | Overview, EQL, query, executivo/PDF | Relatorios |
| `/api/v1/ai-insights/`, `/api/ai/` | Analise por IA | Analitica/inteligencia |
| `/api/v1/intelligence/` | Pipeline, timeline, KPIs, gargalos, riscos, predicoes, score, sumario executivo, conhecimento, enrichment | Inteligencia operacional |
| `/api/v1/actions/`, `/api/actions/` | Fila, gerar, aprovar, rejeitar e executar decisoes | Operacao assistida/gestao |
| `/api/v1/value/`, `/api/value/` | Valor por dashboard, projetos, times, acoes e tendencias | Gestao/relatorios executivos |
| `/api/v1/learning/`, `/api/learning/` | Aprendizado, padroes, playbooks, grafo, memoria, maturidade | Gestao/conhecimento |
| `/api/v1/traces/`, `/api/traces/` | Observabilidade, traces, insights e dashboard | Administrativa/diagnostico |
| `/api/v1/evolution/`, `/api/evolution/` | Versao, compatibilidade, impacto, pipeline, flags, rollback, historico | Administrativa/plataforma |
| `/api/v1/settings/` | Navegacao, workspace, Trello, OpenAI | Configuracoes |
| `/api/v1/users/` | Login, logout, usuario atual, permissoes | Administrativa/autenticacao |
| `/admin/` | Admin Django | Administrativa tecnica |

## 2. Jornada do usuario

### Usuario novo

1. Entrar no sistema.
2. Configurar workspace e credenciais essenciais em `Configuracoes`.
3. Conectar Trello e validar board em `Integracoes`.
4. Executar primeira sincronizacao.
5. Conferir se ha dados no `Dashboard`.
6. Explorar `Analises` para entender status, volume, gaps e insights.
7. Gerar `Relatorios` para consumo executivo.
8. Ajustar OpenAI/configuracoes quando usar insights ou automacoes.

### Usuario recorrente

1. Abrir `Dashboard` para leitura rapida do estado operacional.
2. Usar `Integracoes` apenas quando houver necessidade de sincronizar, trocar board ou resolver conexao.
3. Ir para `Analises` quando precisar investigar causas.
4. Ir para `Relatorios` quando precisar exportar ou comunicar resultado.
5. Usar `Configuracoes` somente para manutencao administrativa.

### Fluxos secundarios

| Fluxo | Sequencia natural | Dependencias |
| --- | --- | --- |
| Sincronizacao de dados | Configuracoes Trello -> Integracoes -> Sync -> Dashboard/Analises | Credenciais Trello e board ativo |
| Geracao de relatorio | Integracoes com dados -> Relatorios -> Baixar PDF | Sync concluido e permissao `reports.generate` |
| Investigacao operacional | Dashboard -> Analises -> Relatorios | Dados canonicos sincronizados |
| Ajuste administrativo | Configuracoes -> Workspace/Trello/OpenAI -> validar Dashboard | Permissao `settings.manage` |
| Automacao futura | Analises/Inteligencia -> Acoes -> Aprovacao/Execucao -> Aprendizado | Dados, IA configurada, regras de permissao |

## 3. Dependencias entre modulos

- `Configuracoes` alimenta Trello/OpenAI/workspace.
- `Integracoes` depende de credenciais e produz dados sincronizados.
- `Dashboard`, `Analises` e `Relatorios` dependem de dados do Trello.
- `Relatorios` depende de `Integracoes` e de permissao de geracao.
- `AI Insights`, `Intelligence`, `Actions`, `Learning` e `Value` dependem de dados canonicos e, em alguns casos, OpenAI.
- `Traces` e `Evolution` sao suporte/diagnostico de plataforma, nao deveriam competir com fluxos operacionais no topo do menu.

## 4. Arquitetura proposta do sidebar

### Estrutura implementada agora, sem quebrar rotas

```text
Dashboard

Operacao
└── Integracoes

Inteligencia e Relatorios
├── Analises
└── Relatorios

Administracao
└── Configuracoes
```

Justificativa:

- `Dashboard` fica isolado no topo porque e o ponto de entrada recorrente e reduz um clique.
- `Integracoes` fica em `Operacao` porque e uma etapa operacional de ingestao/sync, nao apenas uma configuracao tecnica.
- `Analises` vem antes de `Relatorios` porque investigar precede exportar.
- `Configuracoes` sai do fluxo diario e fica em `Administracao`.

### Estrutura alvo quando as telas backend ganharem UI dedicada

```text
Dashboard

Operacao
├── Integracoes
├── Fontes de Dados
├── Sincronizacao
└── Acoes Assistidas

Gestao
├── Valor de Negocio
├── Projetos
├── Times
├── Aprendizado
└── Playbooks

Inteligencia
├── Analises
├── KPIs
├── Gargalos
├── Riscos
├── Predicoes
├── Timeline
└── Conhecimento

Relatorios
├── Executivo
├── Consultas EQL
├── Exportacoes
└── Historico

Administracao
├── Configuracoes
├── Usuarios e Permissoes
├── Observabilidade
├── Evolucao da Plataforma
└── Admin Tecnico
```

## 5. Regras de UX aplicadas

- Prioridade por frequencia: Dashboard no topo, configuracoes no fim.
- Fluxo por objetivo: operar -> analisar -> reportar -> administrar.
- Baixa profundidade: no maximo um nivel de dropdown.
- Estado do accordion persistido em `localStorage`.
- Grupo ativo sempre expandido.
- Suporte a multiplos grupos abertos.
- Rota atual destacada pelo `pathname`.
- Rotas existentes mantidas; a mudanca e visual/organizacional.

## 6. Componentes alterados

- `frontend/src/shared/navigation/menu.ts`: adiciona `SIDEBAR_NAV_GROUPS`.
- `frontend/src/layouts/Sidebar.tsx`: renderiza accordion/dropdown responsivo.
- `frontend/src/shared/navigation/menu.test.ts`: valida ordem agrupada.
- `apps/navigation.py`: expoe `TIP_SIDEBAR_NAV_GROUPS` para clientes server-driven.
- `apps/settings/views.py`: endpoint de navegacao retorna `items` e `groups`.
- `apps/interfaces.py`: adiciona contrato de grupo de navegacao.
- `apps/users/tests/test_permissions.py`: valida agrupamento backend.

## 7. Estrategia de migracao

1. Manter todas as rotas atuais.
2. Continuar retornando `items` no endpoint `/api/v1/settings/navigation/`.
3. Adicionar `groups` como campo novo e opcional para novos clientes.
4. Migrar o frontend para consumir grupos estaticos agora e, depois, grupos server-driven.
5. Criar paginas dedicadas apenas quando houver UI real para os endpoints hoje API-only.
6. Ao criar novas paginas, adiciona-las primeiro ao registry e depois ao grupo de jornada correspondente.
7. Validar permissao por item, nao por grupo, para evitar esconder secoes com filhos parcialmente acessiveis.

## 8. Impacto esperado

- Menos ambiguidade entre analise, relatorio e configuracao.
- Melhor onboarding: o usuario entende que precisa configurar/conectar antes de analisar.
- Menos ruido para usuarios recorrentes: Dashboard continua imediato.
- Sidebar preparado para crescer sem virar uma lista longa e tecnica.
- Possibilidade de evoluir para menu server-driven sem quebrar clientes atuais.
