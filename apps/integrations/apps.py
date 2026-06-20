from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.integrations"
    label = "tip_integrations"
    verbose_name = "TIP Integrations"

    def ready(self) -> None:
        # Import adapters so they self-register in the global registry.
        from apps.integrations.adapters import clickup, jira  # noqa: F401
        from apps.integrations.trello import adapter  # noqa: F401
