from django.urls import path

from apps.reports import views

urlpatterns = [
    path("", views.ReportsOverviewView.as_view(), name="reports-overview"),
    path("executive/", views.CanonicalExecutiveReportView.as_view(), name="reports-executive"),
]
