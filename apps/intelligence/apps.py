from django.apps import AppConfig


class IntelligenceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.intelligence"
    label = "tip_intelligence"
    verbose_name = "EOR Intelligence Engine"

    def ready(self) -> None:
        from apps.intelligence.providers import trello  # noqa: F401
