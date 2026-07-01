# Report Output Audit

## Escopo

Auditoria da saida final do `report_query` antes da reconstrução de output desta sprint.

Restricoes respeitadas:

- nenhuma nova engine;
- nenhum KPI novo de motor analitico;
- nenhuma alteracao em DAL, OLE, BVE, Discovery, Executive Story ou CIC;
- nenhuma remocao de dados antigos ou compatibilidade.

## Fonte auditada

- Executor: `apps/intelligence/services/report_query/engine/executor.py`
- Exportadores: `apps/intelligence/services/report_query/exporters/formats.py`
- Gate: `apps/intelligence/management/commands/validate_report_quality.py`
- Fixture local sem banco: `validate_report_quality --fixture --json`
- Teste de saida real com dados ORM em SQLite: `apps.intelligence.tests.test_report_output_rebuild`

Observacao: o PostgreSQL local em `localhost:5433` estava indisponivel durante a validacao. A geracao real de teste foi executada com `EOR_TESTING=true`, que usa banco de teste em memoria e dados Trello ORM criados pelo teste.

## JSON

### Antes

O JSON carregava dados ricos, mas a estrutura principal ainda parecia orientada a pipeline:

- `data`;
- `metrics`;
- `analytical`;
- `executive_narrative`;
- `discovery`;
- `executive_story`;
- `cards`.

Problemas observados:

- nao havia contrato explicito de 3 camadas;
- tabelas executivas obrigatorias nao eram uma estrutura de primeira classe;
- rankings nao eram um bloco formal;
- `CommercialReportScore` nao existia como contrato da saida final;
- o anexo analitico existia de forma dispersa nos blocos tecnicos.

### Depois

O JSON passou a expor um contrato final de apresentacao:

- `report_output`;
- `executive_brief`;
- `management_diagnosis`;
- `analytical_appendix`;
- `executive_tables`;
- `rankings`;
- `commercial_report_score`.

Compatibilidade mantida: os blocos antigos continuam presentes.

## Markdown

### Antes

O Markdown ja carregava blocos executivos, mas ainda tinha leitura longa e pouco hierarquizada.

Lacunas:

- indice limitado;
- tabelas obrigatorias ausentes como contrato;
- rankings ausentes;
- anexo analitico pouco separado;
- recomendacoes e evidencias apareciam, mas sem formato forte para auditoria rapida.

### Depois

O Markdown agora abre com:

- indice;
- Executive Brief;
- Diagnostico Gerencial;
- Historia Executiva;
- Tabelas Executivas;
- Rankings;
- Decisoes Prioritarias;
- Plano de Acao;
- Anexo Analitico.

Tabelas obrigatorias adicionadas:

- KPIs principais;
- Top categorias;
- Top membros;
- Gargalos;
- Decisoes.

## PDF

### Antes

O PDF era valido e gerado, mas simples.

Lacunas:

- pouca aparencia de capa executiva;
- KPIs sem contrato visual claro;
- validacao automatica dependia apenas de `content_type` e tamanho;
- pouco sinal de se o PDF continha capa, cards de KPI ou conclusao executiva.

### Depois

O PDF passou a declarar contrato visual no payload do export:

- `sections`: Capa, Executive Brief, KPIs, Diagnostico Gerencial, Anexo Analitico;
- `visual_contract.cover = true`;
- `visual_contract.kpi_cards = true`;
- `visual_contract.executive_tables = true` quando tabelas existem;
- `visual_contract.executive_conclusion = true`.

Limitacao mantida: a validacao automatica ainda nao extrai texto do binario PDF. O controle e feito por metadados do export e testes de geracao.

## PPTX

### Antes

O PPTX atual e um outline JSON com content type de PPTX, nao um deck binario real.

Lacunas:

- ordem de slides nao seguia a estrutura de diretoria solicitada;
- nao havia slide de capa;
- gargalos e anexo nao eram slides obrigatorios;
- o formato ainda nao e visualmente um `.pptx` final.

### Depois

O outline passou a conter os slides obrigatorios:

1. Capa
2. Executive Brief
3. Scorecard Executivo
4. Top 3 Drivers
5. Riscos se Nada Mudar
6. Gargalos
7. Decisoes recomendadas
8. Plano de Acao
9. Anexo Analitico

Compatibilidade mantida: os slides reconhecidos pelo validador anterior continuam no outline, incluindo Historia Executiva, Decisoes Prioritarias e Descobertas.

## Avaliacao por criterio

| Criterio | Antes | Depois |
| --- | --- | --- |
| Clareza | Media | Alta |
| Aparencia | Simples | Melhor estruturada; PDF ainda limitado |
| Objetividade | Parcial | Forte no Executive Brief |
| Utilidade para gestor | Boa, mas dispersa | Alta, com decisoes, riscos e acoes no topo |
| Qualidade das tabelas | Baixa | Tabelas obrigatorias presentes |
| Qualidade dos graficos | Limitada | Nao alterada nesta sprint |
| Profundidade das recomendacoes | Boa, mas espalhada | Melhor exposta com evidencias |
| Leitura em 2 minutos | Dificil | Suportada pelo Executive Brief |
| Leitura em 15 minutos | Possivel | Suportada pelo Anexo Analitico |

## Resultado do gate

Comando:

```powershell
$env:EOR_TESTING='true'; .\.venv\Scripts\python.exe manage.py validate_report_quality --fixture --json
```

Resultado:

- status: PASS;
- DecisionValueScore: 100;
- classificacao: executivo;
- exports JSON, Markdown, PDF e PPTX presentes;
- blocos executivos presentes nos exports.

## Limitacoes

- O PDF ainda nao e validado por extracao textual do binario.
- O PPTX segue como outline JSON, nao deck binario final.
- A validacao com banco real nao foi executada porque `localhost:5433` recusou conexao.
- Graficos nao foram recriados para evitar nova engine ou novos KPIs.
