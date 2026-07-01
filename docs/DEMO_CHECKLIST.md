# Demo Checklist

Data: 2026-06-27

## Ambiente

- [ ] Docker Desktop aberto.
- [ ] PostgreSQL responde em `127.0.0.1:5433`.
- [ ] Redis responde em `127.0.0.1:6379`.
- [ ] Migrations aplicadas.
- [ ] `EOR_TESTING` nao esta ativo no runtime real.
- [ ] `DAL_AUTO_EXECUTION=false`.
- [ ] `POCL_ENABLED=false` para demo manual.

## Backend

- [ ] `python manage.py validate_eor_workspace --json` retorna `status=ready`.
- [ ] `python manage.py check` retorna sem issues.
- [ ] Backend responde em `http://127.0.0.1:8000`.
- [ ] `/health/` retorna 200.
- [ ] `/api/v1/settings/` retorna 200.
- [ ] `/api/v1/data-sources/trello/status/` retorna 200.
- [ ] `/api/pilot/dashboard/` retorna 200.

## Frontend

- [ ] `frontend/.env.local` aponta para `http://127.0.0.1:8000`.
- [ ] `npx tsc --noEmit` passa.
- [ ] `npm run build` passa.
- [ ] Frontend responde em `http://127.0.0.1:3000/login`.
- [ ] `/favicon.ico` retorna 200.
- [ ] Login abre sem warning `Cannot update Router while rendering LoginPage`.
- [ ] Console nao mostra `ERR_CONNECTION_REFUSED`.
- [ ] Aviso `cz-shortcut-listen`, se aparecer, foi validado como extensao.

## Quality Gate

- [ ] `EOR_TESTING=true validate_report_quality --fixture --compare-baseline --json` retorna PASS.
- [ ] `DecisionValueScore` dentro do baseline.
- [ ] `ReportQualityScore` dentro do baseline.
- [ ] `ReportIntelligenceScore` dentro do baseline.
- [ ] `ExecutiveStoryQualityScore` dentro do baseline.

## Relatorio Sample

- [ ] `docs/samples/reports/executive_report_sample.json` existe.
- [ ] `docs/samples/reports/executive_report_sample.md` existe.
- [ ] `docs/samples/reports/executive_report_sample.pdf` existe.
- [ ] `docs/samples/reports/executive_report_sample.pptx` existe.
- [ ] PDF abre.
- [ ] PPTX abre.
- [ ] `REPORT_SAMPLE_REVIEW.md` existe.

## Demo Operacional

- [ ] Dashboard carrega.
- [ ] Settings carrega.
- [ ] Integrations mostra status Trello.
- [ ] Reports abre.
- [ ] Dashboard piloto responde.
- [ ] Relatorio executivo fixture pode ser explicado.
- [ ] Decisoes recomendadas aparecem com evidencia.
- [ ] Riscos principais aparecem com prioridade.
- [ ] Plano de acao aparece com dono/prazo quando aplicavel.

## Go / No-Go Da Demo

GO se:

- [ ] Backend 200.
- [ ] Frontend 200.
- [ ] Favicon 200.
- [ ] Endpoints principais 200.
- [ ] Quality gate PASS.
- [ ] Sample disponivel.
- [ ] PDF/PPTX abrem.
- [ ] Console sem erros criticos.

NO-GO se:

- [ ] Backend indisponivel.
- [ ] Frontend indisponivel.
- [ ] `ERR_CONNECTION_REFUSED` persiste.
- [ ] Quality gate FAIL.
- [ ] Sample comercial ausente.
- [ ] PDF/PPTX nao abrem.
- [ ] Console mostra erro critico que impede uso.
