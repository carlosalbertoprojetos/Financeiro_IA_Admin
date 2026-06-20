from django.apps import AppConfig


class DataSourcesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.data_sources"
    label = "tip_data_sources"
    verbose_name = "TIP Data Sources"
