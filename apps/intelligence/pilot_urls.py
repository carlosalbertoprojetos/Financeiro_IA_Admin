from django.urls import path

from apps.intelligence.views_pilot import (
    PilotActivateView,
    PilotDailyCycleView,
    PilotDecisionStreamView,
    PilotDashboardView,
    PilotEvaluateView,
    PilotFeedbackView,
    PilotFollowupsView,
    PilotReportView,
    PilotStatusView,
)

urlpatterns = [
    path("", PilotStatusView.as_view(), name="pilot-status"),
    path("dashboard/", PilotDashboardView.as_view(), name="pilot-dashboard"),
    path("activate/", PilotActivateView.as_view(), name="pilot-activate"),
    path("stream/", PilotDecisionStreamView.as_view(), name="pilot-stream"),
    path("cycle/", PilotDailyCycleView.as_view(), name="pilot-cycle"),
    path("feedback/", PilotFeedbackView.as_view(), name="pilot-feedback"),
    path("followups/", PilotFollowupsView.as_view(), name="pilot-followups"),
    path("report/", PilotReportView.as_view(), name="pilot-report"),
    path("evaluate/", PilotEvaluateView.as_view(), name="pilot-evaluate"),
]
