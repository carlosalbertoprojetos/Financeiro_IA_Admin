# TIP Frontend

Dashboard Next.js para inteligência operacional.

## Setup

```bash
cd frontend
npm install
copy .env.local.example .env.local
```

Edite `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_DEFAULT_BOARD_ID=seu_board_id
```

## Rodar

Backend Django em `http://127.0.0.1:8000`, depois:

```bash
npm run dev
```

Abra `http://localhost:3000`.

## Funcionalidades

- Overview KPIs (health score, lead/cycle time, delay rate)
- Gráficos: throughput, status, KPIs de tempo, aging por status, taxas
- Filtros: período (day/week), colaborador, prioridade (via labels Trello)

## API consumida

- `/api/dashboard/overview/`
- `/api/dashboard/productivity/`
- `/api/dashboard/bottlenecks/`
- `/api/analytics/metrics/cards/`
