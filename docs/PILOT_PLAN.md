# Pilot Plan - EOR Controlled Pilot

Data: 2026-06-27

## Objetivo

Validar se o EOR RC-1 melhora decisoes reais de operacao em um board real supervisionado, medindo clareza, tempo economizado, riscos identificados, decisao humana e impacto observado.

## Escopo

- 1 board operacional real ou board real supervisionado.
- 1 equipe operacional.
- 5 a 10 dias corridos de operacao.
- Relatorios executivos, discovery, executive story, quality gate, DAL em modo human-in-the-loop, OLE/BVE com dados observados.

Fora de escopo:

- automacao sem aprovacao humana;
- novos conectores;
- marketplace;
- licensing;
- multi-tenant produtivo;
- novas engines.

## Duracao Sugerida

7 dias.

Minimo aceito: 5 dias.

Maximo recomendado para piloto RC-1: 10 dias.

## Boards Participantes

Definir antes de ativar:

| Campo | Valor |
| --- | --- |
| Board ID | A definir |
| Board name | A definir |
| Equipe | A definir |
| Gestor responsavel | A definir |
| Operador EOR | A definir |
| Sponsor executivo | A definir |

## Responsaveis

- Gestor operacional: aprova, rejeita ou modifica decisoes.
- Operador EOR: executa ciclos, gera relatorios e registra evidencias.
- Sponsor executivo: avalia valor percebido e decisao de continuidade.
- Responsavel tecnico: monitora saude, logs e qualidade.

## Criterios de Sucesso

- 100% das acoes passam por aprovacao humana.
- Pelo menos 5 relatorios executivos gerados no periodo.
- Pelo menos 60% das decisoes recomendadas aceitas ou modificadas.
- Gestor relata economia de tempo.
- Pelo menos 3 riscos relevantes identificados com evidencia.
- Nenhum incidente de acao automatica indevida.
- Feedback registrado para todas as decisoes apresentadas.

## Criterios de Interrupcao

- Qualquer acao executada sem aprovacao humana.
- Vazamento ou mistura de dados entre boards/clientes.
- Falha recorrente na geracao de relatorio por 2 dias consecutivos.
- Gestor considera as recomendacoes nao confiaveis por 2 ciclos consecutivos.
- Performance inviabiliza uso operacional.

## Riscos

- Board com dados insuficientes para gerar evidencias.
- Gestor nao registrar feedback.
- PostgreSQL/Redis/workers reais nao estarem estaveis em staging.
- Relatorios demorarem em boards grandes.
- Valor financeiro nao poder ser observado no periodo.

## Plano de Rollback

1. Pausar o piloto.
2. Desativar execucao de ciclos automaticos.
3. Manter `DAL_AUTO_EXECUTION=false`.
4. Preservar logs, relatorios e feedbacks.
5. Registrar motivo de interrupcao.
6. Voltar ao uso apenas consultivo dos relatorios.
7. Gerar `PILOT_EXIT_REPORT_TEMPLATE.md` preenchido.

## Comandos de Preparacao

```powershell
python manage.py validate_eor_workspace --json
$env:EOR_TESTING='true'; python manage.py validate_report_quality --fixture --compare-baseline --json
$env:EOR_TESTING='true'; python manage.py test
```
