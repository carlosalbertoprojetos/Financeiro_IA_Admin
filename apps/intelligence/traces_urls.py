from django.urls import path

from apps.intelligence.views_traces import (
    TraceByQueryView,
    TraceDashboardView,
    TraceDetailView,
    TraceInsightsView,
    TracesOverviewView,
)

urlpatterns = [
    path("", TracesOverviewView.as_view(), name="traces-overview"),
    path("insights/", TraceInsightsView.as_view(), name="traces-insights"),
    path("dashboard/", TraceDashboardView.as_view(), name="traces-dashboard"),
    path("query/<str:query_id>/", TraceByQueryView.as_view(), name="traces-by-query"),
    path("<str:trace_id>/", TraceDetailView.as_view(), name="traces-detail"),
]
