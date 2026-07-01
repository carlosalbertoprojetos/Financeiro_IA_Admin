# Executive Document Generator

## Objetivo

O Executive Document Generator (EDG) e a camada de publicacao do EOR.

Ele transforma exclusivamente o `output_contract` em documentos executivos. Nao cria analise, nao cria KPI e nao acessa Trello.

## Separacao

| Camada | Responsabilidade |
| --- | --- |
| Inteligencia | Produzir fatos, metricas, historia, riscos e decisoes |
| Output Contract | Organizar a saida final em contrato de apresentacao |
| EDG | Publicar documentos corporativos a partir do contrato |

## Estrutura

```text
apps/intelligence/services/document_generator/
    builders/
    templates/
    styles/
    charts/
    assets/
    validators/
    exporters/
```

## PresentationModel

Todos os builders consomem `PresentationModel`.

Campos principais:

- capa;
- executive brief;
- scorecard;
- KPIs;
- tabelas;
- graficos;
- rankings;
- timeline;
- riscos;
- decisoes;
- plano de acao;
- anexos.

## Builders

| Builder | Saida | Observacao |
| --- | --- | --- |
| `executive_pdf.py` | PDF | Usa ReportLab |
| `executive_pptx.py` | PPTX | Gera OOXML editavel sem acessar dados externos |
| `executive_xlsx.py` | XLSX | Gera workbook OOXML com abas executivas |
| `executive_docx.py` | DOCX | Gera documento OOXML formal |

## Restricao principal

Entrada unica permitida:

```python
PresentationModel.from_output_contract(output_contract)
```

Nenhum builder deve importar modelos Trello, queryset, DAL, Discovery, Executive Story ou qualquer motor analitico.
