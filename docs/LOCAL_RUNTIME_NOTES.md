# Local Runtime Notes

Data: 2026-06-27

## Objetivo

Registrar o diagnostico e o checklist para executar backend Django e frontend Next.js juntos no ambiente local do EOR.

Runbook principal:

```text
docs/LOCAL_DEMO_RUNBOOK.md
```

Checklist de demo:

```text
docs/DEMO_CHECKLIST.md
```

Verificador opcional:

```powershell
.\scripts\local_demo_check.ps1
```

## Workspace

Validacao executada:

```text
python manage.py validate_eor_workspace --json
```

Resultado:

```text
workspace=EOR
status=ready
model_version=1.1
failures=0
warnings=0
```

## Backend Local

Comandos:

```text
docker compose up -d
python manage.py check
python manage.py runserver 127.0.0.1:8000
```

Endpoints que o frontend usa:

```text
GET http://127.0.0.1:8000/api/v1/settings/
GET http://127.0.0.1:8000/api/v1/data-sources/trello/status/
```

Rotas confirmadas:

- `/api/v1/settings/` vem de `apps.settings.urls`.
- `/api/v1/data-sources/trello/status/` vem de `apps.data_sources.urls`.

Se o console do navegador mostrar `ERR_CONNECTION_REFUSED`, a causa esperada e backend indisponivel na porta `8000`, nao erro de CORS.

Diagnostico local executado:

```text
Test-NetConnection 127.0.0.1 -Port 5433
```

Resultado observado:

```text
TcpTestSucceeded=False
```

Sem PostgreSQL ativo em `localhost:5433`, chamadas que consultam configuracoes/conexoes podem ficar aguardando conexao de banco ou falhar. Subir o Docker antes do backend.

Depois de `docker compose up -d`, a porta respondeu:

```text
TcpTestSucceeded=True
```

O banco local tambem precisava de migracoes pendentes:

```text
python manage.py migrate
```

Migracoes aplicadas no diagnostico:

- `core.0003_initial`
- `tip_integrations.0007_integrationconnection_tenant`
- `tip_intelligence.0012_customeronboardingstate`
- `tip_intelligence.0013_rename_action_log_decision_idx_action_exec_decisio_361c63_idx_and_more`
- `tip_settings.0002_alter_workspaceconfig_openai_model`
- `trello.0002_board_tenant`

## Banco Local

O arquivo `.env` aponta para:

```text
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=tip_backend
```

Para runtime real, nao usar `EOR_TESTING=true`. Esse modo troca o banco para SQLite de teste e deve ficar restrito a comandos de teste/CI.

Comando recomendado do projeto:

```text
Executar_EOR.bat
```

Esse script sobe PostgreSQL/Redis via Docker, libera portas `8000` e `3000`, inicia Django e Next.js.

## Frontend Local

Arquivo:

```text
frontend/.env.local
```

Configuracao:

```text
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

`NEXT_PUBLIC_API_BASE_URL` e o nome preferencial. `NEXT_PUBLIC_API_URL` continua suportado por compatibilidade.

Comando:

```text
cd frontend
npm run dev
```

## LoginPage

O redirecionamento de usuario autenticado deve ocorrer em `useEffect`, nao durante render.

Motivo:

```text
Cannot update a component (`Router`) while rendering `LoginPage`
```

## Favicon

O frontend declara:

```text
icons.icon=/favicon.ico
```

O arquivo local esperado e:

```text
frontend/public/favicon.ico
```

## Hydration Warning

Aviso observado:

```text
Extra attributes from server: cz-shortcut-listen
```

Diagnostico:

Esse atributo costuma ser injetado por extensao de navegador. Quando apenas `cz-shortcut-listen` aparece, nao alterar codigo do EOR. Validar em janela anonima ou com extensoes desativadas.

## Checklist De Execucao

1. Verificar se PostgreSQL local esta disponivel em `localhost:5433`.
2. Se necessario, executar `docker compose up -d`.
3. Executar `python manage.py check`.
4. Executar `python manage.py runserver 127.0.0.1:8000`.
5. Testar `http://127.0.0.1:8000/api/v1/settings/`.
6. Testar `http://127.0.0.1:8000/api/v1/data-sources/trello/status/`.
7. Executar `cd frontend`.
8. Executar `npm run dev`.
9. Abrir o login.
10. Confirmar que nao ha `ERR_CONNECTION_REFUSED`.
11. Confirmar que o redirect do login nao gera warning de update durante render.
12. Confirmar que `/favicon.ico` nao retorna 404.
13. Ignorar `cz-shortcut-listen` se desaparecer com extensoes desativadas.

## Validacao Realizada

Backend:

```text
GET /api/v1/settings/ -> 200
GET /api/v1/data-sources/trello/status/ -> 200
```

Frontend:

```text
GET /login -> 200
GET /favicon.ico -> 200 image/x-icon
```

Build:

```text
npm run build -> OK
```

Observacao:

```text
npm run lint
```

O comando abriu o assistente interativo do Next.js porque o projeto ainda nao possui configuracao ESLint inicializada. Nenhuma configuracao nova foi criada nesta correcao para evitar mudanca fora do escopo.
