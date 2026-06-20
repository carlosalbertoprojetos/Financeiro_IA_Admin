# TIP Architecture — Platform Layer

**API v1:** `/api/v1/` — facades over legacy modules (no duplicated business logic).

| App | Path | Delegates to |
|-----|------|--------------|
| `apps.data_sources` | `/api/v1/data-sources/` | `integrations.trello` |
| `apps.dashboards` | `/api/v1/dashboards/` | `dashboard` |
| `apps.analytics` | `/api/v1/analytics/` | `analytics` |
| `apps.reports` | `/api/v1/reports/` | `reports` |
| `apps.ai_insights` | `/api/v1/ai-insights/` | `ai` |
| `apps.exports` | `/api/v1/exports/` | metadata → `reports` |
| `apps.users` | `/api/v1/users/` | placeholder auth |
| `apps.settings` | `/api/v1/settings/` | navigation + config placeholders |

**Legacy APIs preserved:** `/api/dashboard/`, `/api/analytics/`, etc.

See `PROJECT_CLASSIFICATION.md` for full module map.
