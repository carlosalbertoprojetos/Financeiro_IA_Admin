from django.apps import AppConfig


class TipAnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.analytics"
    label = "tip_analytics"
    verbose_name = "TIP Analytics"
