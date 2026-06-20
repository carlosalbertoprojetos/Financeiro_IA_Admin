from rest_framework.response import Response
from rest_framework.views import APIView

from apps.interfaces import module_placeholder


class DataSourcesOverviewView(APIView):
    """Lists available data source connectors."""

    def get(self, request):
        return Response(
            {
                "connectors": [
                    {
                        "id": "trello",
                        "label": "Trello",
                        "status": "active",
                        "connect_path": "/api/v1/data-sources/trello/connect/",
                        "sync_path": "/api/v1/data-sources/trello/sync/",
                        "status_path": "/api/v1/data-sources/trello/status/",
                        "legacy_sync_path": "/api/v1/data-sources/trello/sync/<board_id>/",
                    },
                    {
                        "id": "excel",
                        "label": "Excel",
                        "status": "placeholder",
                        "import_path": "/api/v1/data-sources/excel/",
                    },
                    module_placeholder("csv", message="CSV import — future MVP."),
                    module_placeholder("jira", message="Jira connector — future MVP."),
                    module_placeholder("clickup", message="ClickUp connector — future MVP."),
                    module_placeholder("monday", message="Monday connector — future MVP."),
                ]
            }
        )


class ExcelImportPlaceholderView(APIView):
    """Placeholder for Excel import — Sprint 03."""

    def get(self, request):
        return Response(module_placeholder("excel", legacy_path="/api/v1/data-sources/excel/"))

    def post(self, request):
        return Response(
            module_placeholder(
                "excel",
                message="Excel import not yet implemented. Use Trello sync for now.",
            ),
            status=501,
        )
