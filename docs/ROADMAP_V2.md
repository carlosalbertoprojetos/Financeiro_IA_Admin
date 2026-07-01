# Roadmap V2 - EOR

Data: 2026-06-27

Este roadmap nao implementa novas funcionalidades nesta sprint. Ele organiza a evolucao posterior do EOR apos a consolidacao de produto executivo.

## Melhorias Imediatas

1. Corrigir suite completa de testes.
   - Resolver compatibilidade SQLite/JSONField nos testes canonicos.
   - Corrigir refresh de analytics no worker Trello.
   - Ajustar expectation de eventos da Description Intelligence.

2. Validar board real em staging.
   - Rodar `validate_report_quality --board-id <id> --period LAST_30_DAYS --compare-baseline`.
   - Gerar PDF/PPTX reais de board operacional.
   - Comparar feedback humano com DecisionValueScore.

3. Polir PDF/PPTX para demo comercial.
   - Capa com identidade visual.
   - Pagina de resumo executivo.
   - Slides com menos texto e mais hierarquia visual.
   - Blocos de decisao com destaque.

4. Documentar runbook de demo.
   - Como apresentar.
   - Qual historia contar.
   - Quais perguntas o relatorio responde.
   - Como lidar com limitacoes.

## Melhorias Futuras

1. Multi-tenant produtivo.
   - Tenant canonico.
   - Querysets tenant-aware.
   - Cache isolado.
   - Exports e logs com tenant enforcement.

2. Licensing runtime.
   - Planos aplicados em rotas e features.
   - Auditoria de uso por plano.
   - Alertas de limite.

3. Onboarding guiado.
   - Cadastro.
   - Organizacao.
   - Conexao Trello.
   - Primeiro sync.
   - Primeiro relatorio em menos de 10 minutos.

4. Customer Success Dashboard visual.
   - Valor gerado.
   - Tempo economizado.
   - Riscos tratados.
   - ROI observado.

## Pesquisa

- Como gestores interpretam o Executive Brief em menos de 60 segundos.
- Quais decisoes sao de fato tomadas apos receber o relatorio.
- Qual granularidade de evidencia aumenta confianca sem poluir a leitura.
- Quais indicadores melhor predizem reducao de atraso e retrabalho.
- Como comunicar incerteza e confianca para publico executivo.

## Ideias

- Modo "Board Review Meeting" com roteiro de reuniao.
- Relatorio de uma pagina para diretoria.
- Relatorio detalhado para coordenadores.
- Comparativo entre equipes ou unidades quando houver multi-tenant seguro.
- Biblioteca de playbooks operacionais acionaveis.

## Experimentos

1. Piloto de 5 a 10 dias com uma equipe real.
   - Medir sugestoes aceitas.
   - Medir tempo de decisao.
   - Medir atrasos antes/depois.

2. Teste A/B de narrativa.
   - Relatorio metrico versus relatorio com historia executiva.
   - Medir compreensao e decisao tomada.

3. Validacao de score comercial.
   - Coletar nota de gestores.
   - Comparar com CommercialReportScore.
   - Calibrar criterios.

4. ROI observado.
   - Medir horas economizadas.
   - Medir retrabalho evitado.
   - Medir melhora de SLA.

## Marco de V2

EOR V2 deve provar valor continuo em operacao real:

- relatorio entendido em menos de 5 minutos;
- decisoes gerenciais tomadas a partir do relatorio;
- impacto observado em SLA, atraso ou retrabalho;
- isolamento SaaS seguro;
- onboarding comercial repetivel.
