from django.urls import path

from reports.views import ExecutiveReportView

urlpatterns = [
    path("executive/", ExecutiveReportView.as_view(), name="reports-executive"),
]
