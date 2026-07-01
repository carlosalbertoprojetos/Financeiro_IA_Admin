# Document Validation

## Objetivo

Validar que documentos gerados pelo EDG sao abertos e possuem estrutura minima esperada.

## PDF

Checks:

- assinatura `%PDF`;
- paginacao;
- secoes esperadas.

## PPTX

Checks:

- pacote OOXML com `ppt/presentation.xml`;
- slides editaveis com shapes de texto;
- elementos posicionados;
- 12 slides minimos.

## XLSX

Checks:

- pacote OOXML com `xl/workbook.xml`;
- abas obrigatorias;
- filtros;
- congelamento de paineis;
- formulas validas.

## DOCX

Checks:

- pacote OOXML com `word/document.xml`;
- paragrafos e tabelas;
- secoes executivas.

## Golden File Tests

Os testes evitam regressao silenciosa comparando:

- numero de slides;
- presenca de secoes;
- abas;
- tabelas;
- validadores por formato.

Suite principal:

```powershell
$env:EOR_TESTING='true'; .\.venv\Scripts\python.exe manage.py test apps.intelligence.tests.test_executive_document_generator -v 2
```
