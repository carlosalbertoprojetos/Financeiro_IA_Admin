# Export Architecture

## Fluxo

```text
output_contract
    -> PresentationModel
    -> Chart Factory
    -> Builders
    -> Validators
    -> Demo Package
```

## Entradas e saidas

| Componente | Entrada | Saida |
| --- | --- | --- |
| PresentationModel | `output_contract` | modelo intermediario |
| Chart Factory | `output_contract` | especificacoes de graficos |
| PDF Builder | `PresentationModel` | bytes PDF |
| PPTX Builder | `PresentationModel` | bytes PPTX |
| XLSX Builder | `PresentationModel` | bytes XLSX |
| DOCX Builder | `PresentationModel` | bytes DOCX |
| Demo Package | `output_contract` | pasta com artefatos |

## Demo Package

Comando:

```powershell
python manage.py generate_demo_package --json
```

Saida:

```text
docs/demo_package/
    executive_report.pdf
    executive_report.pptx
    executive_report.xlsx
    executive_report.docx
    executive_report.json
    executive_report.md
    validation.json
```

## Garantia arquitetural

O EDG nao acessa Trello, nao executa query e nao chama motores analiticos. O pacote demo usa fixture apenas para obter um `output_contract` demonstrativo.
