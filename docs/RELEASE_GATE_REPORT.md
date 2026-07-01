# Release Gate Report

Status: **WARNING**

```json
{
  "status": "WARNING",
  "checks": [
    {
      "name": "workspace",
      "status": "READY",
      "payload": {
        "workspace": "EOR",
        "root": "C:\\Arquivos\\Trello\\ExecutiveOperationReport\\EOP",
        "status": "ready",
        "model_version": "1.1",
        "expected_model_version": "1.1",
        "summary": {
          "checks": 27,
          "failures": 0,
          "warnings": 0
        },
        "checks": [
          {
            "name": "file:manage.py",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "file:README.md",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "file:requirements.txt",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "file:docker-compose.yml",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "file:Executar_EOR.bat",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "dir:ai",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "dir:analytics",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "dir:apps",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "dir:core",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "dir:dashboard",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "dir:frontend",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "dir:integrations",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "dir:reports",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "dir:tip_backend",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "dir:apps/intelligence/services/semantic_layer",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "dir:apps/intelligence/services/timeline",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "dir:apps/intelligence/services/risk_engine",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "dir:apps/intelligence/services/decision_layer",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "dir:apps/intelligence/services/organizational_learning",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "dir:apps/intelligence/services/business_value",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "dir:apps/intelligence/services/pilot",
            "status": "ok",
            "detail": "present"
          },
          {
            "name": "installed_app:apps.integrations",
            "status": "ok",
            "detail": "registered"
          },
          {
            "name": "installed_app:apps.intelligence",
            "status": "ok",
            "detail": "registered"
          },
          {
            "name": "installed_app:apps.settings",
            "status": "ok",
            "detail": "registered"
          },
          {
            "name": "installed_app:integrations.trello",
            "status": "ok",
            "detail": "registered"
          },
          {
            "name": "installed_app:rest_framework",
            "status": "ok",
            "detail": "registered"
          },
          {
            "name": "model_version",
            "status": "ok",
            "detail": "current=1.1; expected=1.1"
          }
        ]
      }
    },
    {
      "name": "migrations",
      "status": "READY",
      "payload": {
        "status": "ok",
        "unapplied_migrations": []
      }
    },
    {
      "name": "health",
      "status": "WARNING",
      "payload": {
        "service": "eor",
        "status": "degraded",
        "timestamp": "2026-06-26T23:01:50.153987+00:00",
        "checks": [
          {
            "name": "database",
            "status": "ok",
            "latency_ms": 0,
            "detail": "connection established",
            "error": "",
            "last_success_at": "2026-06-26T23:01:50.152988+00:00",
            "severity": "info"
          },
          {
            "name": "redis",
            "status": "warn",
            "latency_ms": 0,
            "detail": "REDIS_CACHE_URL not configured; using local cache",
            "error": "",
            "last_success_at": null,
            "severity": "medium"
          },
          {
            "name": "cache",
            "status": "ok",
            "latency_ms": 0,
            "detail": "read/write",
            "error": "",
            "last_success_at": "2026-06-26T23:01:50.153987+00:00",
            "severity": "info"
          },
          {
            "name": "queues",
            "status": "ok",
            "latency_ms": 0,
            "detail": "integration backend=local_db",
            "error": "",
            "last_success_at": "2026-06-26T23:01:50.153987+00:00",
            "severity": "info"
          },
          {
            "name": "scheduler",
            "status": "warn",
            "latency_ms": 0,
            "detail": "no scheduler schedule configured",
            "error": "",
            "last_success_at": null,
            "severity": "low"
          },
          {
            "name": "trello",
            "status": "ok",
            "latency_ms": 0,
            "detail": "credentials configured",
            "error": "",
            "last_success_at": "2026-06-26T23:01:50.153987+00:00",
            "severity": "info"
          },
          {
            "name": "ai",
            "status": "warn",
            "latency_ms": 0,
            "detail": "AI key missing; no new engine added",
            "error": "",
            "last_success_at": null,
            "severity": "low"
          },
          {
            "name": "storage",
            "status": "ok",
            "latency_ms": 0,
            "detail": "static_root=C:\\Arquivos\\Trello\\ExecutiveOperationReport\\EOP\\staticfiles",
            "error": "",
            "last_success_at": "2026-06-26T23:01:50.153987+00:00",
            "severity": "info"
          },
          {
            "name": "workers",
            "status": "ok",
            "latency_ms": 0,
            "detail": "broker=redis://localhost:6379/0",
            "error": "",
            "last_success_at": "2026-06-26T23:01:50.153987+00:00",
            "severity": "info"
          }
        ]
      }
    },
    {
      "name": "tenant_isolation",
      "status": "WARNING",
      "payload": {
        "status": "attention_required",
        "checks": [
          {
            "area": "data_model",
            "status": "guarded",
            "evidence": "Tenant model exists; Trello Board and IntegrationConnection are tenant-bound. Card/Action inherit scope through Board.",
            "recommendation": "Backfill tenant_id for existing boards before paid pilot."
          },
          {
            "area": "queries",
            "status": "guarded",
            "evidence": "Paid system APIs require X-Tenant-Id; onboarding board selection rejects cross-tenant boards.",
            "recommendation": "Continue migrating legacy intelligence endpoints to assert_board_belongs_to_tenant."
          },
          {
            "area": "cache",
            "status": "warning",
            "evidence": "Global cache key prefix exists; product readiness APIs do not cache tenant data.",
            "recommendation": "Prefix all cache keys with tenant_id and board_id."
          },
          {
            "area": "actions",
            "status": "guarded",
            "evidence": "DAL auto execution is disabled by default and approval flow exists.",
            "recommendation": "Keep human approval mandatory until tenant scoped audit is complete."
          }
        ]
      }
    },
    {
      "name": "licensing",
      "status": "READY",
      "payload": {
        "status": "ok",
        "plans": [
          {
            "name": "starter",
            "limits": {
              "boards": 2,
              "users": 5,
              "cards_analyzed": 1000
            },
            "modules": [
              "dashboard",
              "trello_sync",
              "executive_report"
            ],
            "connectors": [
              "trello"
            ],
            "exports": false,
            "marketplace": false
          },
          {
            "name": "professional",
            "limits": {
              "boards": 10,
              "users": 25,
              "cards_analyzed": 10000
            },
            "modules": [
              "dashboard",
              "trello_sync",
              "report_query",
              "dal_approval",
              "value_dashboard"
            ],
            "connectors": [
              "trello",
              "jira",
              "clickup"
            ],
            "exports": true,
            "marketplace": false
          },
          {
            "name": "business",
            "limits": {
              "boards": 50,
              "users": 100,
              "cards_analyzed": 100000
            },
            "modules": [
              "all_professional",
              "pocl",
              "ole",
              "bve",
              "self_diagnostics",
              "customer_success"
            ],
            "connectors": [
              "trello",
              "jira",
              "clickup",
              "asana",
              "monday",
              "github_projects"
            ],
            "exports": true,
            "marketplace": true
          },
          {
            "name": "enterprise",
            "limits": {
              "boards": -1,
              "users": -1,
              "cards_analyzed": -1
            },
            "modules": [
              "all",
              "sso_ready",
              "custom_connectors",
              "advanced_audit",
              "marketplace"
            ],
            "connectors": [
              "all"
            ],
            "exports": true,
            "marketplace": true
          }
        ],
        "enforcement": {
          "mode": "architecture_ready",
          "runtime_guard_required": false,
          "note": "Plan catalog is enforced by require_plan_feature/check_plan_limits."
        }
      }
    },
    {
      "name": "connectors",
      "status": "WARNING",
      "payload": {
        "status": "warning",
        "interface": "WorkManagementProvider + BaseIntegrationAdapter",
        "registered_providers": [
          "asana",
          "azure_devops",
          "clickup",
          "github_projects",
          "jira",
          "monday",
          "notion",
          "planner",
          "trello"
        ],
        "connectors": [
          {
            "id": "trello",
            "label": "Trello",
            "status": "available",
            "adapter": "TrelloAdapter",
            "registered": true,
            "production_ready": true,
            "next_step": "Monitor credentials, sync freshness and rate limits."
          },
          {
            "id": "jira",
            "label": "Jira",
            "status": "registered_placeholder",
            "adapter": "JiraAdapter",
            "registered": true,
            "production_ready": false,
            "next_step": "Implement authenticate/fetch/map with provider API and contract tests."
          },
          {
            "id": "clickup",
            "label": "ClickUp",
            "status": "registered_placeholder",
            "adapter": "ClickUpAdapter",
            "registered": true,
            "production_ready": false,
            "next_step": "Implement authenticate/fetch/map with provider API and contract tests."
          },
          {
            "id": "monday",
            "label": "Monday",
            "status": "registered_placeholder",
            "adapter": "MondayAdapter",
            "registered": true,
            "production_ready": false,
            "next_step": "Implement authenticate/fetch/map with provider API and contract tests."
          },
          {
            "id": "asana",
            "label": "Asana",
            "status": "registered_placeholder",
            "adapter": "AsanaAdapter",
            "registered": true,
            "production_ready": false,
            "next_step": "Implement authenticate/fetch/map with provider API and contract tests."
          },
          {
            "id": "azure_devops",
            "label": "Azure DevOps",
            "status": "registered_placeholder",
            "adapter": "AzureDevOpsAdapter",
            "registered": true,
            "production_ready": false,
            "next_step": "Implement authenticate/fetch/map with provider API and contract tests."
          },
          {
            "id": "github_projects",
            "label": "GitHub Projects",
            "status": "registered_placeholder",
            "adapter": "GitHubProjectsAdapter",
            "registered": true,
            "production_ready": false,
            "next_step": "Implement authenticate/fetch/map with provider API and contract tests."
          },
          {
            "id": "planner",
            "label": "Planner",
            "status": "registered_placeholder",
            "adapter": "PlannerAdapter",
            "registered": true,
            "production_ready": false,
            "next_step": "Implement authenticate/fetch/map with provider API and contract tests."
          },
          {
            "id": "notion",
            "label": "Notion",
            "status": "registered_placeholder",
            "adapter": "NotionAdapter",
            "registered": true,
            "production_ready": false,
            "next_step": "Implement authenticate/fetch/map with provider API and contract tests."
          }
        ]
      }
    },
    {
      "name": "critical_tests",
      "status": "READY",
      "payload": {
        "status": "ok",
        "returncode": 0,
        "output_tail": "Creating test database for alias 'default'...\n\nFound 13 test(s).\nSystem check identified no issues (0 silenced).\n..WARNING 2026-06-26 20:01:54,250 log Forbidden: /api/system/onboarding/select-boards/\n.WARNING 2026-06-26 20:01:54,256 log Forbidden: /api/system/usage/\n.WARNING 2026-06-26 20:01:54,264 log Forbidden: /api/system/marketplace/\n.WARNING 2026-06-26 20:01:54,279 log Payment Required: /api/system/onboarding/select-boards/\n........\n----------------------------------------------------------------------\nRan 13 tests in 0.161s\n\nOK\nDestroying test database for alias 'default'...\n\n"
      }
    }
  ]
}
```
