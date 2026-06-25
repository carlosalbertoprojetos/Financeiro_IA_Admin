from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", include("core.urls")),
    path("api/dashboard/", include("dashboard.urls")),
    path("api/analytics/", include("analytics.urls")),
    path("api/reports/", include("reports.urls")),
    path("api/traces/", include("apps.intelligence.traces_urls")),
    path("api/evolution/", include("apps.intelligence.evolution_urls")),
    path("api/actions/", include("apps.intelligence.actions_urls")),
    path("api/learning/", include("apps.intelligence.learning_urls")),
    path("api/value/", include("apps.intelligence.value_urls")),
    path("api/pilot/", include("apps.intelligence.pilot_urls")),
    path("api/ai/", include("ai.urls")),
    path("api/integrations/trello/", include("integrations.trello.urls")),
    path("api/v1/", include("apps.urls")),
]
