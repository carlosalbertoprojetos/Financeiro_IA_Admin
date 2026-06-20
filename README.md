# tip_backend

Backend Django modular para SaaS de inteligência operacional baseado em dados do Trello.

## Dependências

- Python 3.10+
- PostgreSQL 16
- Redis 7 (preparado para Celery)

### Pacotes Python

| Pacote | Uso |
|--------|-----|
| Django | Framework web |
| djangorestframework | API REST |
| psycopg2-binary | Driver PostgreSQL |
| python-dotenv | Variáveis de ambiente |
| celery | Tarefas assíncronas |
| redis | Broker/backend Celery |

## Estrutura do sistema

```
EOP/
├── manage.py
├── requirements.txt
├── docker-compose.yml          # PostgreSQL + Redis
├── .env.example
├── tip_backend/                # Configuração do projeto Django
│   ├── settings/
│   │   ├── base.py               # Settings compartilhados
│   │   ├── dev.py                # Desenvolvimento
│   │   └── prod.py               # Produção
│   ├── urls.py                   # Rotas globais
│   ├── celery.py                 # Config Celery
│   ├── wsgi.py
│   └── asgi.py
├── core/                         # Configurações gerais e base models
├── integrations/
│   └── trello/                   # Conector Trello API
├── analytics/                    # Métricas e KPIs
├── reports/                      # Relatórios PDF e estruturados
├── ai/                           # Análise com OpenAI API
└── dashboard/                    # API para frontend
```

### Camadas (ordem de implementação)

1. **Estrutura** — skeleton Django (este projeto)
2. **Ingestão** — Trello → PostgreSQL
3. **Inteligência** — KPIs → IA → PDF

## Como rodar

### 1. Clonar e preparar ambiente

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/macOS
```

Edite `.env` conforme necessário.

### 3. Subir PostgreSQL e Redis

```bash
docker compose up -d
```

### 4. Migrar e rodar

```bash
python manage.py migrate
python manage.py runserver
```

### 5. Verificar healthcheck

```bash
curl http://127.0.0.1:8000/health/
```

Resposta esperada:

```json
{
  "status": "ok",
  "service": "tip_backend",
  "database": "ok",
  "timestamp": "2026-06-17T12:00:00+00:00"
}
```

## Endpoints

| Rota | Descrição |
|------|-----------|
| `/health/` | Healthcheck do serviço |
| `/admin/` | Django Admin |
| `/api/dashboard/` | API dashboard (futuro) |
| `/api/analytics/` | API analytics (futuro) |
| `/api/reports/` | API reports (futuro) |
| `/api/ai/` | API IA (futuro) |
| `/api/integrations/trello/` | API Trello (futuro) |

## Settings

| Ambiente | Módulo |
|----------|--------|
| Desenvolvimento | `tip_backend.settings.dev` |
| Produção | `tip_backend.settings.prod` |

Defina via variável `DJANGO_SETTINGS_MODULE` no `.env`.

## Celery (preparado)

```bash
celery -A tip_backend worker -l info
```

Requer Redis em execução (`docker compose up -d`).

## Próximos passos

- Camada 2: ingestão Trello → PostgreSQL
- Camada 3: KPIs, análise IA e geração de PDF
