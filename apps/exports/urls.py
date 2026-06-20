from django.urls import path

from apps.exports import views

urlpatterns = [
    path("", views.ExportsOverviewView.as_view(), name="exports-overview"),
    path("pdf/", views.PdfExportInfoView.as_view(), name="exports-pdf-info"),
]
