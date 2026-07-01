# Customer Validation Guide

Data: 2026-06-27

## Objetivo

Conduzir validacoes do EOR com usuarios reais para medir valor percebido, confianca, utilidade decisoria e comportamento real de uso.

Esta etapa nao busca validar arquitetura, criar novas funcionalidades ou defender hipoteses internas. O objetivo e descobrir se gestores, coordenadores e operadores usariam o EOR novamente, confiariam nos relatorios e perceberiam valor suficiente para justificar compra ou continuidade do piloto.

## Escopo Da Validacao

Inclui:

- Executive Brief.
- Executive Story.
- Discovery Insights.
- Dashboard.
- Exports.
- Scorecard.
- Benchmark.
- Relatorios executivos gerados no piloto.
- Decisoes recomendadas e feedback humano.

Nao inclui:

- Novas engines.
- Mudancas arquiteturais.
- Automacoes sem aprovacao humana.
- Promessas comerciais ainda nao suportadas pelo produto.
- Roadmap baseado em opiniao sem evidencia.

## Preparacao Antes Da Reuniao

Checklist:

- Confirmar participante, cargo e responsabilidade operacional.
- Confirmar board, periodo e relatorio a ser usado.
- Validar que dados sensiveis podem ser exibidos.
- Preparar amostra de relatorio, dashboard e exports.
- Abrir formularios de observacao e feedback.
- Definir observador responsavel por registrar tempo, telas, duvidas e comentarios.
- Reforcar que o EOR apoia decisoes, mas nao executa acoes automaticamente.

## Roteiro Da Reuniao

Duracao sugerida: 45 a 60 minutos.

1. Contexto inicial, 5 minutos.
   - Explicar objetivo da validacao.
   - Confirmar papel do participante.
   - Perguntar como hoje ele analisa risco, atraso, SLA e prioridades.

2. Demonstracao guiada, 10 minutos.
   - Mostrar dashboard.
   - Abrir relatorio executivo.
   - Destacar Executive Story, Top Drivers, riscos e decisoes recomendadas.

3. Tarefa observada, 20 minutos.
   - Pedir que o usuario encontre os maiores riscos do periodo.
   - Pedir que identifique a decisao mais urgente.
   - Pedir que exporte ou compartilhe uma conclusao.
   - Observar sem conduzir demais.

4. Discussao de valor, 15 minutos.
   - Investigar se o relatorio economiza tempo.
   - Investigar se revelou algo novo.
   - Investigar confianca nas recomendacoes.
   - Investigar disposicao de uso recorrente ou pagamento.

5. Fechamento, 5 minutos.
   - Registrar principais pontos.
   - Confirmar proximos passos.
   - Pedir autorizacao para usar feedback anonimo em sintese de produto.

## Roteiro De Apresentacao

Mensagem base:

```text
O EOR e uma plataforma de inteligencia operacional para apoiar decisoes de gestao. Nesta validacao queremos observar se os relatorios ajudam voce a entender o que aconteceu, por que importa, quais riscos existem e quais decisoes tomar. Nenhuma acao sera automatizada sem aprovacao humana.
```

Sequencia recomendada:

1. Situar periodo e board analisado.
2. Mostrar o resumo executivo.
3. Mostrar a historia executiva do periodo.
4. Mostrar Top 3 Drivers.
5. Mostrar riscos e descobertas.
6. Mostrar decisoes recomendadas.
7. Mostrar plano de acao.
8. Mostrar export disponivel.

## Perguntas De Descoberta

Antes de mostrar o produto:

- Como voce identifica prioridades hoje?
- Quanto tempo leva para preparar uma leitura executiva do board?
- Quais sinais de risco costumam passar despercebidos?
- O que torna um relatorio confiavel para voce?

Durante o uso:

- O que voce procurou primeiro?
- O que ficou claro rapidamente?
- Onde voce ficou em duvida?
- Que parte pareceu mais util para decidir?
- Que informacao pareceu pouco confiavel ou excessiva?

Depois do uso:

- Voce usaria este relatorio novamente?
- Voce recomendaria para outro gestor?
- Voce pagaria por isso? Em quais condicoes?
- Qual decisao ficou mais facil?
- O que impediria a contratacao?
- O que deveria ser removido?

## Como Registrar Feedback

Regras:

- Registrar frase real do usuario sempre que possivel.
- Separar comportamento observado de opiniao declarada.
- Nao transformar sugestao isolada em roadmap sem evidencia adicional.
- Associar cada insight a participante, perfil, contexto e tela.
- Registrar se o usuario descobriu o valor sozinho ou precisou de explicacao.
- Registrar decisoes aceitas, rejeitadas ou modificadas com motivo.

Fontes obrigatorias:

- `docs/USABILITY_OBSERVATION_FORM.md`
- `docs/FEATURE_ADOPTION_TRACKER.md`
- `docs/DECISION_TRACKING_TEMPLATE.md`
- `docs/VALUE_ASSESSMENT_FORM.md`
- `docs/CUSTOMER_INSIGHTS_SYNTHESIS.md`

## Criterios De Sucesso

Sinais fortes:

- Usuario entende a primeira pagina sem explicacao longa.
- Usuario identifica ao menos uma decisao acionavel.
- Usuario percebe economia de tempo.
- Usuario confia nas evidencias apresentadas.
- Usuario aceitaria usar o EOR em rotina real.
- Usuario indicaria o produto para outro gestor.
- Usuario declara condicao clara de pagamento ou continuidade.

Sinais de alerta:

- Usuario nao entende a historia executiva.
- Usuario nao consegue ligar recomendacao a evidencia.
- Usuario considera o relatorio longo demais para decisao.
- Usuario nao confia nos dados.
- Usuario nao consegue citar uma decisao facilitada.
- Usuario ve valor apenas como curiosidade, nao como ferramenta operacional.

## Regra Para Roadmap

Nenhum item deve entrar no backlog como P0, P1 ou P2 sem evidencia registrada.

Evidencia minima:

- Observacao direta de uso.
- Comentario espontaneo.
- Decisao aceita, rejeitada ou modificada.
- Dor recorrente entre usuarios.
- Impacto claro em tempo, confianca, risco, SLA ou retrabalho.
