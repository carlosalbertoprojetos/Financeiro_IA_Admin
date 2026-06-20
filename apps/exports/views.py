from rest_framework.response import Response
from rest_framework.views import APIView


class ExportsOverviewView(APIView):
    """Export formats catalog — PDF generation delegates to reports module."""

    def get(self, request):
        return Response(
            {
                "module": "exports",
                "status": "active",
                "formats": [
                    {
                        "id": "pdf_executive",
                        "label": "PDF Executivo",
                        "status": "active",
                        "generate_path": "/api/v1/reports/executive/",
                        "info_path": "/api/v1/exports/pdf/",
                    },
                    {
                        "id": "csv",
                        "label": "CSV",
                        "status": "placeholder",
                    },
                    {
                        "id": "xlsx",
                        "label": "Excel Export",
                        "status": "placeholder",
                    },
                ],
            }
        )


class PdfExportInfoView(APIView):
    """Describes PDF export without duplicating report generation logic."""

    def get(self, request):
        return Response(
            {
                "format": "pdf",
                "engine": "reports.engine.pdf_builder",
                "method": "POST",
                "path": "/api/v1/reports/executive/",
                "legacy_path": "/api/reports/executive/",
                "note": "Use reports endpoint — no parallel PDF logic in exports module.",
            }
        )
