from django.urls import path

from apps.intelligence import views

urlpatterns = [
    path("", views.IntelligenceOverviewView.as_view(), name="intelligence-overview"),
    path("pipeline/", views.IntelligencePipelineView.as_view(), name="intelligence-pipeline"),
    path("timeline/", views.TimelineView.as_view(), name="intelligence-timeline"),
    path("kpis/", views.KPIView.as_view(), name="intelligence-kpis"),
    path("bottlenecks/", views.BottleneckView.as_view(), name="intelligence-bottlenecks"),
    path("risks/", views.RiskView.as_view(), name="intelligence-risks"),
    path("predictions/", views.PredictiveView.as_view(), name="intelligence-predictions"),
    path("score/", views.OperationalScoreView.as_view(), name="intelligence-score"),
    path("executive-summary/", views.ExecutiveSummaryView.as_view(), name="intelligence-executive-summary"),
    path("report/", views.ExecutiveReportView.as_view(), name="intelligence-report"),
    path("knowledge/", views.KnowledgeBaseView.as_view(), name="intelligence-knowledge"),
    path("dashboard/", views.ExecutiveDashboardView.as_view(), name="intelligence-dashboard"),
    path("enrichment/", views.EnrichmentView.as_view(), name="intelligence-enrichment"),
]
