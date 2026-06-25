from django.urls import path

from apps.intelligence.views_value import (
    ValueActionsView,
    ValueDashboardView,
    ValueOverviewView,
    ValueProjectsView,
    ValueTeamsView,
    ValueTrendsView,
)

urlpatterns = [
    path("", ValueOverviewView.as_view(), name="value-overview"),
    path("dashboard/", ValueDashboardView.as_view(), name="value-dashboard"),
    path("projects/", ValueProjectsView.as_view(), name="value-projects"),
    path("teams/", ValueTeamsView.as_view(), name="value-teams"),
    path("actions/", ValueActionsView.as_view(), name="value-actions"),
    path("trends/", ValueTrendsView.as_view(), name="value-trends"),
]
