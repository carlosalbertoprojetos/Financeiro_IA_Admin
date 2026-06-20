from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", include("core.urls")),
    path("api/dashboard/", include("dashboard.urls")),
    path("api/analytics/", include("analytics.urls")),
    path("api/reports/", include("reports.urls")),
    path("api/ai/", include("ai.urls")),
    path("api/integrations/trello/", include("integrations.trello.urls")),
    path("api/v1/", include("apps.urls")),
]
