# Local Demo Runbook

Data: 2026-06-27

## Objetivo

Subir o EOR localmente para demo ou piloto supervisionado, validar backend/frontend e confirmar que os relatorios executivos estao prontos para apresentacao sem erros criticos.

Este runbook nao cria funcionalidades e nao altera arquitetura. Ele apenas descreve o caminho operacional local.

## 1. Pre-Requisitos

- Windows com PowerShell.
- Python 3.10+.
- Ambiente virtual em `.venv`.
- Dependencias Python instaladas com `pip install -r requirements.txt`.
- Node.js e npm.
- Dependencias do frontend instaladas em `frontend/node_modules`.
- Docker Desktop ativo.
- Portas livres:
  - Backend: `8000`.
  - Frontend: `3000`.
  - PostgreSQL local: `5433`.
  - Redis local: `6379`.

## 2. Variaveis `.env`

Arquivo esperado na raiz:

```text
.env
```

Variaveis essenciais:

```text
DJANGO_SETTINGS_MODULE=tip_backend.settings.dev
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=tip_backend
POSTGRES_USER=tip_user
POSTGRES_PASSWORD=tip_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5433

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

DAL_AUTO_EXECUTION=false
POCL_ENABLED=false
```

Frontend:

```text
frontend/.env.local
```

Variaveis:

```text
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

`NEXT_PUBLIC_API_BASE_URL` e o nome preferencial. `NEXT_PUBLIC_API_URL` continua aceito por compatibilidade.

## 3. Subir PostgreSQL E Redis

Na raiz do projeto:

```powershell
docker compose up -d
```

Validar PostgreSQL:

```powershell
Test-NetConnection 127.0.0.1 -Port 5433
```

Resultado esperado:

```text
TcpTestSucceeded=True
```

## 4. Rodar Migrations

```powershell
.\.venv\Scripts\python.exe manage.py migrate
```

Se `.venv` nao existir, criar e instalar dependencias antes de continuar:

```powershell
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
```

## 5. Iniciar Backend

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Validar:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health/ -UseBasicParsing
```

## 6. Iniciar Frontend

Em outro terminal:

```powershell
cd frontend
npm run dev:3000
```

Abrir:

```text
http://127.0.0.1:3000/login
```

## 7. Validar Endpoints

Com o backend rodando:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/v1/settings/ -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8000/api/v1/data-sources/trello/status/ -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8000/api/pilot/dashboard/ -UseBasicParsing
```

Resultados esperados:

```text
/api/v1/settings/ -> 200
/api/v1/data-sources/trello/status/ -> 200
/api/pilot/dashboard/ -> 200
```

Frontend:

```powershell
Invoke-WebRequest http://127.0.0.1:3000/login -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:3000/favicon.ico -UseBasicParsing
```

Resultados esperados:

```text
/login -> 200
/favicon.ico -> 200 image/x-icon
```

## 8. Validar Relatorio Fixture

```powershell
$env:EOR_TESTING='true'
.\.venv\Scripts\python.exe manage.py validate_report_quality --fixture --compare-baseline --json
Remove-Item Env:\EOR_TESTING
```

Resultado esperado:

```text
status=PASS
```

## 9. Validar Quality Gate

Comando minimo para demo local:

```powershell
$env:EOR_TESTING='true'
.\.venv\Scripts\python.exe manage.py validate_report_quality --fixture --compare-baseline --json
Remove-Item Env:\EOR_TESTING
```

O quality gate deve confirmar:

- `DecisionValueScore` dentro do baseline.
- `ReportQualityScore` dentro do baseline.
- `ReportIntelligenceScore` dentro do baseline.
- `ExecutiveStoryQualityScore` dentro do baseline.
- Blocos executivos obrigatorios presentes.
- Exports executivos presentes.

## 10. Validar Sample Comercial

Confirmar que existem:

```text
docs/samples/reports/executive_report_sample.json
docs/samples/reports/executive_report_sample.md
docs/samples/reports/executive_report_sample.pdf
docs/samples/reports/executive_report_sample.pptx
docs/samples/reports/REPORT_SAMPLE_REVIEW.md
```

Abrir manualmente:

- PDF.
- PPTX.

Confirmar que a primeira parte comunica:

- Historia executiva.
- Top 3 Drivers.
- Decisoes prioritarias.
- Riscos.
- Plano de acao.

## 11. Validacao Automatizada Opcional

```powershell
.\scripts\local_demo_check.ps1
```

Para pular build do frontend:

```powershell
.\scripts\local_demo_check.ps1 -SkipFrontendBuild
```

## 12. Parar Ambiente

Encerrar janelas:

- Backend Django.
- Frontend Next.js.

Parar containers:

```powershell
docker compose down
```

Para manter dados do banco local, nao remover volumes.

## 13. Problemas Comuns

### ERR_CONNECTION_REFUSED

Causa provavel:

- Backend nao esta rodando em `127.0.0.1:8000`.
- Porta 8000 esta ocupada.
- PostgreSQL nao subiu e o backend nao inicializou corretamente.

Correcao:

```powershell
docker compose up -d
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

### PostgreSQL 5433 indisponivel

Validar:

```powershell
Test-NetConnection 127.0.0.1 -Port 5433
```

Correcao:

```powershell
docker compose up -d
```

### Warning `cz-shortcut-listen`

Causa provavel:

- Extensao de navegador.

Validacao:

- Abrir em janela anonima.
- Desativar extensoes.

Nao alterar codigo quando esse for o unico atributo extra.

### `npm run lint` pede configuracao

O projeto ainda nao possui configuracao ESLint inicializada. Para demo local, usar:

```powershell
npx tsc --noEmit
npm run build
```

## 14. Caminho Rapido

```powershell
docker compose up -d
.\.venv\Scripts\python.exe manage.py migrate
.\scripts\local_demo_check.ps1
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Em outro terminal:

```powershell
cd frontend
npm run dev:3000
```
