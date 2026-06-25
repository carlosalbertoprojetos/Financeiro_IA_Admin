from django.urls import include, path

from apps.platform_views import PlatformOverviewView

urlpatterns = [
    path("", PlatformOverviewView.as_view(), name="platform-overview"),
    path("integrations/", include("apps.integrations.urls")),
    path("data-sources/", include("apps.data_sources.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("reports/", include("apps.reports.urls")),
    path("dashboards/", include("apps.dashboards.urls")),
    path("ai-insights/", include("apps.ai_insights.urls")),
    path("exports/", include("apps.exports.urls")),
    path("users/", include("apps.users.urls")),
    path("settings/", include("apps.settings.urls")),
    path("intelligence/", include("apps.intelligence.urls")),
    path("traces/", include("apps.intelligence.traces_urls")),
    path("evolution/", include("apps.intelligence.evolution_urls")),
    path("actions/", include("apps.intelligence.actions_urls")),
    path("learning/", include("apps.intelligence.learning_urls")),
    path("value/", include("apps.intelligence.value_urls")),
    path("pilot/", include("apps.intelligence.pilot_urls")),
]
