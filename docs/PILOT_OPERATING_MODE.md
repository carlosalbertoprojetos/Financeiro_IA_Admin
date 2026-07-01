# Pilot Operating Mode

Data: 2026-06-27

## Modo Seguro Obrigatorio

```text
DAL_AUTO_EXECUTION=false
```

Regras:

- Todas as acoes exigem aprovacao humana.
- Nenhuma acao destrutiva permitida.
- Nenhuma automacao direta em Trello sem aprovacao.
- Feedback obrigatorio para cada decisao.
- Logging completo de relatorios, decisoes, feedbacks, execucoes e follow-ups.
- Impacto deve ser observado, nao inferido.

## Limite Diario

Limite recomendado: ate 10 acoes sugeridas por dia.

Objetivo: evitar sobrecarga do gestor e preservar qualidade da revisao humana.

## Fluxo Diario

1. Gerar relatorio executivo.
2. Revisar Top 3 Drivers.
3. Revisar decisoes recomendadas.
4. Aprovar, rejeitar ou modificar cada decisao.
5. Registrar feedback.
6. Executar manualmente a acao aprovada.
7. Agendar follow-up de impacto.
8. Registrar resultados observados.

## Guardrails

- Baixa confianca deve ser apresentada como baixa confianca.
- Decisao sem evidencia nao deve ser executada.
- Recomendacao rejeitada deve ter motivo registrado.
- Acao modificada deve guardar acao original e acao final.
- Todo output para cliente deve indicar periodo e board analisado.

## Endpoint de Acompanhamento

```text
GET /api/pilot/dashboard/?board_id=<BOARD_ID>
```

Campos principais:

- `usage`
- `decisions`
- `risks`
- `impact`
- `quality`
- `operating_mode`
