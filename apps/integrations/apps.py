from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.integrations"
    label = "tip_integrations"
    verbose_name = "TIP Integrations"

    def ready(self) -> None:
        # Import adapters so they self-register in the global registry.
        from apps.integrations.adapters import (  # noqa: F401
            asana,
            azure_devops,
            clickup,
            github_projects,
            jira,
            monday,
            notion,
            planner,
        )
        from apps.integrations.trello import adapter  # noqa: F401
