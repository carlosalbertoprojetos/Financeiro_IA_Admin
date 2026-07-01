# Report Export Validation

## Objetivo

Validar se os exports carregam valor decisorio, nao apenas dados brutos.

Formatos avaliados:

- JSON
- Markdown
- PDF
- PPTX

## Perguntas obrigatorias

Cada export deve responder:

1. O que aconteceu?
2. Por que importa?
3. Quais sao os 3 drivers?
4. Quais decisoes tomar?
5. Quais riscos permanecem?
6. Qual plano de acao seguir?

## Checklist por formato

| Formato | O que aconteceu | Por que importa | Top 3 drivers | Decisoes | Riscos | Plano de acao |
| --- | --- | --- | --- | --- | --- | --- |
| JSON | `executive_story.period_story` | `business_implications` | `key_drivers` | `decision_ready_summary` | `story_structure.riscos_se_nada_mudar` | `action_plan` |
| Markdown | `História Executiva` | `História Executiva` e `Narrativa Executiva` | `Top 3 Drivers` | `Decisões Prioritárias` | `Cenário provável` e riscos | `Plano de Ação` |
| PDF | primeira pagina executiva | historia e drivers | resumo de drivers | resumo de decisoes | linhas de risco/discovery | linhas de acao |
| PPTX | slide `História Executiva` | slide `História Executiva` | slide `Top 3 Drivers` | slide `Decisões Prioritárias` | slide `Riscos se Nada Mudar` | slide `Plano de Ação` |

## Regras automatizadas

O validador considera export valido quando:

- JSON contem blocos executivos no payload;
- Markdown contem:
  - `História Executiva`
  - `Top 3 Drivers`
  - `Decisões Prioritárias`
  - `Plano de Ação`
- PPTX outline contem os slides:
  - `História Executiva`
  - `Top 3 Drivers`
  - `Decisões Prioritárias`
  - `Plano de Ação`
- PDF possui `content_type=application/pdf` e tamanho maior que zero.

## Comando de validacao

```powershell
python manage.py validate_report_quality --board-id <BOARD_ID> --json
```

O resultado inclui:

```json
{
  "export_validation": {
    "json": {},
    "markdown": {},
    "pdf": {},
    "pptx": {}
  }
}
```

## Gate

O gate falha quando:

- qualquer export obrigatorio esta ausente;
- Markdown ou PPTX nao carregam blocos executivos;
- PDF nao e gerado;
- JSON nao contem blocos executivos.

## Evidencias esperadas

Cada formato retorna evidencias objetivas:

- termos encontrados no Markdown;
- slides encontrados no PPTX;
- tipo/tamanho do PDF;
- blocos presentes no JSON.

## Limitacoes

- A validacao automatica do PDF nao extrai texto do binario.
- O PPTX atual e outline JSON com `content_type` de PPTX, conforme implementacao existente.
- A validacao foca valor decisorio, nao fidelidade visual.
