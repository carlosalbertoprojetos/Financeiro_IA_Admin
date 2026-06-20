from django.urls import path

from analytics.views import (
    CardsMetricsView,
    GapsMetricsView,
    MetricsView,
    OverviewMetricsView,
    TeamMetricsView,
)

urlpatterns = [
    path("metrics/", MetricsView.as_view(), name="analytics-metrics"),
    path("metrics/overview/", OverviewMetricsView.as_view(), name="analytics-metrics-overview"),
    path("metrics/team/", TeamMetricsView.as_view(), name="analytics-metrics-team"),
    path("metrics/cards/", CardsMetricsView.as_view(), name="analytics-metrics-cards"),
    path("metrics/gaps/", GapsMetricsView.as_view(), name="analytics-metrics-gaps"),
]
