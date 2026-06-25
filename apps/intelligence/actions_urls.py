from django.urls import path

from apps.intelligence.views_actions import (
    ActionQueueView,
    ActionsOverviewView,
    ApproveActionView,
    DecisionDetailView,
    ExecuteActionView,
    GenerateDecisionsView,
    RejectActionView,
)

urlpatterns = [
    path("", ActionsOverviewView.as_view(), name="actions-overview"),
    path("queue/", ActionQueueView.as_view(), name="actions-queue"),
    path("generate/", GenerateDecisionsView.as_view(), name="actions-generate"),
    path("execute/", ExecuteActionView.as_view(), name="actions-execute"),
    path("approve/", ApproveActionView.as_view(), name="actions-approve"),
    path("reject/", RejectActionView.as_view(), name="actions-reject"),
    path("decisions/<str:decision_id>/", DecisionDetailView.as_view(), name="actions-decision-detail"),
]
