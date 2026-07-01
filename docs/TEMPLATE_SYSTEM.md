# Template System

## Temas

O EDG suporta quatro temas:

- Corporate Theme;
- Minimal Theme;
- Executive Theme;
- Dark Theme.

## Regra

Tema altera apenas apresentacao.

Tema nunca altera:

- metricas;
- decisoes;
- evidencias;
- rankings;
- riscos;
- ordem logica do documento.

## Configuracao

Temas ficam em:

```text
apps/intelligence/services/document_generator/templates/themes.py
```

Branding fica em:

```text
apps/intelligence/services/document_generator/styles/branding.py
```

Campos de branding:

- logotipo;
- cores;
- rodape;
- cabecalho;
- empresa;
- cliente;
- confidencialidade;
- versao.

## Uso

```python
from apps.intelligence.services.document_generator.templates import get_theme

theme = get_theme("executive")
```
