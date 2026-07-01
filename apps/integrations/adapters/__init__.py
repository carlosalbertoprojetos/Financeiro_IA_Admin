"""Provider adapters — import modules to register with the global registry."""

from apps.integrations.adapters import (
    asana,
    azure_devops,
    clickup,
    github_projects,
    jira,
    monday,
    notion,
    planner,
    trello,
)

__all__ = [
    "asana",
    "azure_devops",
    "clickup",
    "github_projects",
    "jira",
    "monday",
    "notion",
    "planner",
    "trello",
]
