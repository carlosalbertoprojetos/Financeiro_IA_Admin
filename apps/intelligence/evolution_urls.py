from django.urls import path

from apps.intelligence.views_evolution import (
    EvolutionFlagsView,
    EvolutionHistoryView,
    EvolutionImpactView,
    EvolutionOverviewView,
    EvolutionPipelineView,
    EvolutionRollbackView,
    EvolutionVersionView,
)

urlpatterns = [
    path("", EvolutionOverviewView.as_view(), name="evolution-overview"),
    path("version/", EvolutionVersionView.as_view(), name="evolution-version"),
    path("compatibility/", EvolutionVersionView.as_view(), name="evolution-compatibility"),
    path("impact/", EvolutionImpactView.as_view(), name="evolution-impact"),
    path("pipeline/", EvolutionPipelineView.as_view(), name="evolution-pipeline"),
    path("flags/", EvolutionFlagsView.as_view(), name="evolution-flags"),
    path("rollback/", EvolutionRollbackView.as_view(), name="evolution-rollback"),
    path("history/", EvolutionHistoryView.as_view(), name="evolution-history"),
]
