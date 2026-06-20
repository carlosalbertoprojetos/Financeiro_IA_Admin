from django.urls import include, path

from apps.ai_insights import views

urlpatterns = [
    path("", views.AiInsightsOverviewView.as_view(), name="ai-insights-overview"),
    path("", include("ai.urls")),
]
