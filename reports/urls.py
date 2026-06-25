from django.urls import path

from reports.views import ExecutiveReportView
from apps.intelligence.views_eql import EQLReportView
from apps.intelligence.views_report_query import ReportQueryView

urlpatterns = [
    path("executive/", ExecutiveReportView.as_view(), name="reports-executive"),
    path("eql/", EQLReportView.as_view(), name="reports-eql"),
    path("query/", ReportQueryView.as_view(), name="reports-query"),
]
