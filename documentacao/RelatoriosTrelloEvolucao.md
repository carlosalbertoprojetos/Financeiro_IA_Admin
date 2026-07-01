# Evolucao dos Relatorios Trello

Data da evolucao: 2026-06-27

## O que foi alterado

Esta etapa implementa a primeira evolucao incremental da inteligencia operacional baseada em cards Trello, preservando os relatorios existentes.

Foram adicionados:

- parser contratual para descricoes de cards;
- normalizador intermediario de card Trello;
- novos campos estruturados no mapper canonico;
- novos campos estruturados nas linhas do Report Query;
- testes unitarios focados;
- documentacao de diagnostico e evolucao.

Nenhum campo antigo de relatorio foi removido.

## Arquivos modificados

- `apps/intelligence/services/description_intelligence/__init__.py`
- `apps/intelligence/services/report_query/engine/post_processor.py`
- `apps/integrations/trello/mapper.py`

## Novos modulos criados

- `apps/intelligence/services/description_intelligence/structured_sections.py`
- `apps/intelligence/services/trello_card_intelligence/__init__.py`
- `apps/intelligence/services/trello_card_intelligence/normalizer.py`
- `apps/intelligence/tests/test_structured_trello_reports.py`
- `documentacao/RelatoriosTrelloDiagnostico.md`
- `documentacao/RelatoriosTrelloEvolucao.md`

## Parser da descricao

Funcao principal:

```python
parse_structured_description(text)
```

Estrutura retornada:

```python
{
    "data_solicitacao": None,
    "objetivo": None,
    "contexto": None,
    "atividades": [],
    "resultado_esperado": None,
    "riscos": [],
    "criterios_conclusao": [],
    "resultado_obtido": None,
    "evidencias": [],
    "links": [],
    "metricas": [],
    "raw_description": ""
}
```

O parser aceita:

- titulos em maiusculas/minusculas;
- titulos com dois pontos;
- variacoes como `Objetivos`, `Resultado Esperado`, `Critério de Conclusão`, `Riscos` e `Evidências`;
- linhas em branco em excesso;
- listas com `-`, `*`, `+`, `1.` e `1)`;
- descricoes incompletas ou vazias;
- links e metricas mencionadas no texto.

Campos ausentes retornam `None` ou lista vazia. O parser nao inventa informacao.

## Normalizador de card

Funcao principal:

```python
normalize_trello_card(card, actions=None)
```

Saida principal:

- `id`
- `name`
- `list_name`
- `created_at`
- `due_date`
- `completed_at`
- `labels`
- `members`
- `checklists`
- `checklist_total`
- `checklist_completed`
- `checklist_completion_percent`
- `comments_count`
- `attachments_count`
- `description_sections`
- `links`
- `metrics`
- `risks_count`
- `evidences_count`
- `documentation_completeness_score`

O normalizador usa dados ja disponiveis no modelo legado e no `raw_json`. Se checklists completos nao estiverem no payload, usa `badges.checkItems` e `badges.checkItemsCheck` quando existirem.

## Novos indicadores

### Por tarefa

Adicionados de forma estruturada:

- links extraidos da descricao;
- metricas mencionadas na descricao;
- quantidade de riscos documentados;
- quantidade de evidencias documentadas;
- checklist total;
- checklist concluido;
- percentual de checklist concluido;
- anexos quando disponiveis no `raw_json` ou `badges`;
- indice de completude da documentacao.

### Qualidade

Foi implementado o calculo de completude com 10 campos:

1. objetivo;
2. contexto;
3. atividades;
4. resultado esperado;
5. risco;
6. criterio de conclusao;
7. resultado obtido;
8. evidencias;
9. checklist;
10. responsavel.

Pontuacao:

```text
campos preenchidos / campos avaliados * 100
```

## Integracao com relatorios atuais

### Pipeline canonico

`apps/integrations/trello/mapper.py` agora preserva no `metadata`:

- `description`;
- `description_sections`;
- `links`;
- `metrics`;
- `risks_count`;
- `evidences_count`;
- `checklist_total`;
- `checklist_completed`;
- `checklist_completion_percent`;
- `documentation_completeness_score`.

O formato de `CanonicalTask` nao foi alterado.

### Report Query

`apps/intelligence/services/report_query/engine/post_processor.py` agora adiciona nas linhas de card:

- `description_sections`;
- `documentation_completeness_score`;
- `description_links`;
- `description_metrics`;
- `description_risks_count`;
- `description_evidences_count`;
- `checklist_total`;
- `checklist_completed`;
- `checklist_completion_percent`;
- `attachments_count`.

Campos antigos como `card_id`, `title`, `status`, `labels`, `assignees`, `prefix`, `due_at` e `completed_at` continuam presentes.

## Como executar

Validar workspace:

```powershell
python manage.py validate_eor_workspace --json
```

Rodar testes novos:

```powershell
.\.venv\Scripts\python.exe manage.py test apps.intelligence.tests.test_structured_trello_reports -v 2
```

Rodar testes existentes da inteligencia de descricao:

```powershell
.\.venv\Scripts\python.exe manage.py test apps.intelligence.tests.test_description_intelligence -v 2
```

## Testes executados

```text
.\.venv\Scripts\python.exe manage.py test apps.intelligence.tests.test_structured_trello_reports -v 2
Resultado: 8 testes, OK
```

```text
.\.venv\Scripts\python.exe manage.py test apps.intelligence.tests.test_description_intelligence -v 2
Resultado: 4 testes, OK
```

## Limitacoes conhecidas

- O cliente canonico Trello ainda nao busca membros por card; por isso o score canonico de completude considera `has_owner=False`.
- Checklists completos so sao usados quando ja aparecem em `raw_json`; caso contrario, o normalizador usa badges sinteticos.
- Attachments so sao contados quando aparecem em `raw_json.attachments` ou `badges.attachments`.
- Datas reais de conclusao e movimentacao por lista ainda dependem de actions/timeline e nao foram recalculadas nesta etapa.
- Agregacoes completas por colaborador/equipe e novas secoes de exportacao ainda precisam ser ampliadas em uma etapa posterior.
- Os indicadores por colaborador devem permanecer com nota metodologica: sao operacionais e nao devem ser usados isoladamente para julgamento individual.

## Proximos passos recomendados

1. Integrar os novos campos no `analytical.metrics_pack.quality`.
2. Adicionar secoes dedicadas em Markdown/PDF/PPTX outline para Dados Estruturados da Descricao.
3. Consolidar agregacoes por colaborador e equipe usando `NormalizedTrelloCard`.
4. Avaliar coleta adicional de checklists e attachments via API Trello, com controle de chamadas para evitar custo desnecessario.
5. Definir metodologia unica para data real de conclusao usando actions/listas finais.

## Resumo executivo

### Diagnostico encontrado

O sistema ja possuia dois pipelines Trello: legado, mais rico em actions e historico, e canonico, mais simples e voltado a multi-provider. A descricao dos cards era armazenada, mas nao havia contrato estruturado para transforma-la nas secoes gerenciais solicitadas.

### Melhorias implementadas

Foi criado um parser flexivel para descricoes, um normalizador intermediario de cards, integracao aditiva no mapper canonico e enriquecimento das linhas do Report Query.

### Riscos tecnicos

O maior risco permanece na diferenca entre os pipelines legado e canonico. Alguns indicadores dependem de dados que o canonico ainda nao coleta, principalmente membros, comentarios, checklists completos, anexos e historico de movimentacao.

### Testes executados

Foram executados testes unitarios novos e a suite existente de inteligencia de descricao, ambos com sucesso.

### Pendencias

Ainda faltam agregacoes completas por colaborador/equipe, secoes novas em todos os formatos de exportacao e metodologia consolidada para datas reais de conclusao.

### Recomendacoes

Continuar por evolucoes pequenas, usando o pipeline legado para relatorios ricos e levando campos estruturados ao canonico via `metadata` ate que a coleta canonica seja ampliada.

