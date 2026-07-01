from __future__ import annotations

from apps.integrations.core.registry import registry


CONNECTOR_CATALOG = [
    {"id": "trello", "label": "Trello", "status": "available", "adapter": "TrelloAdapter"},
    {"id": "jira", "label": "Jira", "status": "registered_placeholder", "adapter": "JiraAdapter"},
    {"id": "clickup", "label": "ClickUp", "status": "registered_placeholder", "adapter": "ClickUpAdapter"},
    {"id": "monday", "label": "Monday", "status": "registered_placeholder", "adapter": "MondayAdapter"},
    {"id": "asana", "label": "Asana", "status": "registered_placeholder", "adapter": "AsanaAdapter"},
    {"id": "azure_devops", "label": "Azure DevOps", "status": "registered_placeholder", "adapter": "AzureDevOpsAdapter"},
    {"id": "github_projects", "label": "GitHub Projects", "status": "registered_placeholder", "adapter": "GitHubProjectsAdapter"},
    {"id": "planner", "label": "Planner", "status": "registered_placeholder", "adapter": "PlannerAdapter"},
    {"id": "notion", "label": "Notion", "status": "registered_placeholder", "adapter": "NotionAdapter"},
]


def connector_readiness() -> dict[str, object]:
    registered = set(registry.list_providers())
    connectors = []
    for item in CONNECTOR_CATALOG:
        connector = dict(item)
        connector["registered"] = item["id"] in registered
        if item["status"] != "available":
            connector["production_ready"] = False
            connector["next_step"] = "Implement authenticate/fetch/map with provider API and contract tests."
        else:
            connector["production_ready"] = True
            connector["next_step"] = "Monitor credentials, sync freshness and rate limits."
        connectors.append(connector)
    return {
        "status": "warning",
        "interface": "WorkManagementProvider + BaseIntegrationAdapter",
        "registered_providers": sorted(registered),
        "connectors": connectors,
    }
