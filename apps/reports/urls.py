from django.urls import path

from apps.intelligence.views_eql import EQLReportView
from apps.intelligence.views_report_query import ReportQueryView
from apps.reports import views

urlpatterns = [
    path("", views.ReportsOverviewView.as_view(), name="reports-overview"),
    path("eql/", EQLReportView.as_view(), name="reports-eql"),
    path("query/", ReportQueryView.as_view(), name="reports-query"),
    path("executive/", views.CanonicalExecutiveReportView.as_view(), name="reports-executive"),
]
