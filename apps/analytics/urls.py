from django.urls import include, path

from apps.analytics import views

urlpatterns = [
    path("", views.AnalyticsOverviewView.as_view(), name="analytics-overview"),
    path("metrics/", include("analytics.urls")),
]
