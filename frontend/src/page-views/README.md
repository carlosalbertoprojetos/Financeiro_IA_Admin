# Camada de Páginas TIP (`page-views/`)

Composição de rotas. Next.js App Router fica em `src/app/`.

> **Nota:** A pasta física é `page-views/` porque Next.js reserva `src/pages/` para o Pages Router.
> Imports usam o alias `@/pages/*` → `src/page-views/*`.

## Estrutura

```
src/
├── app/              # Rotas Next.js (re-exportam @/pages/*)
├── page-views/       # Composição: permissões + feature views  (@/pages)
├── features/         # Módulos por domínio
├── shared/           # Auth, permissões, tipos, componentes
└── layouts/          # AppShell, AuthGate
```

| Rota | Compositor | Feature | Permissão |
|------|------------|---------|-----------|
| `/login` | `login.tsx` | — | `auth.login` |
| `/dashboard` | `dashboard.tsx` | `features/dashboards` | `dashboard.view` |
| `/integrations` | `integrations.tsx` | `features/integrations` | `integrations.view` |
| `/analytics` | `analytics.tsx` | `features/analytics` | `analytics.view` |
| `/reports` | `reports.tsx` | `features/reports` | `reports.view` |
| `/settings` | `settings.tsx` | `features/settings` | `settings.view` |
