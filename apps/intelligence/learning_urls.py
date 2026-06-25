from django.urls import path

from apps.intelligence.views_learning import (
    ActionHistoricalStatsView,
    LearningDashboardView,
    LearningKnowledgeGraphView,
    LearningMaturityView,
    LearningMemoryView,
    LearningOverviewView,
    LearningPatternsView,
    LearningPlaybooksView,
)

urlpatterns = [
    path("", LearningOverviewView.as_view(), name="learning-overview"),
    path("dashboard/", LearningDashboardView.as_view(), name="learning-dashboard"),
    path("patterns/", LearningPatternsView.as_view(), name="learning-patterns"),
    path("playbooks/", LearningPlaybooksView.as_view(), name="learning-playbooks"),
    path("knowledge-graph/", LearningKnowledgeGraphView.as_view(), name="learning-knowledge-graph"),
    path("memory/", LearningMemoryView.as_view(), name="learning-memory"),
    path("maturity/", LearningMaturityView.as_view(), name="learning-maturity"),
    path("actions/<str:action_type>/", ActionHistoricalStatsView.as_view(), name="learning-action-stats"),
]
