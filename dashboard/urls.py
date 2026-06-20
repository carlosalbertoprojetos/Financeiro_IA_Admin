from django.urls import path

from dashboard.views import (
    DashboardBottlenecksView,
    DashboardEfficiencyView,
    DashboardOverviewView,
    DashboardProductivityView,
)

urlpatterns = [
    path("overview/", DashboardOverviewView.as_view(), name="dashboard-overview"),
    path("productivity/", DashboardProductivityView.as_view(), name="dashboard-productivity"),
    path("efficiency/", DashboardEfficiencyView.as_view(), name="dashboard-efficiency"),
    path("bottlenecks/", DashboardBottlenecksView.as_view(), name="dashboard-bottlenecks"),
]
