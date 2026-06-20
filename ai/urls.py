from django.urls import path

from ai.views import AnalyzeBoardView

urlpatterns = [
    path("analyze/", AnalyzeBoardView.as_view(), name="ai-analyze"),
]
