from django.urls import path

from apps.dashboards import views

urlpatterns = [
    path("", views.DashboardsOverviewView.as_view(), name="dashboards-overview"),
    path("metrics/", views.CanonicalDashboardMetricsView.as_view(), name="dashboards-metrics"),
    path("analytics/", views.CanonicalAnalyticsView.as_view(), name="dashboards-analytics"),
]
