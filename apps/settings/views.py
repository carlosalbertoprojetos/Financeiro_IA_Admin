from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.integrations.core.exceptions import ConnectionNotFoundError
from apps.integrations.trello.client import TrelloClient
from apps.integrations.trello.connections import save_trello_connection
from apps.integrations.trello.exceptions import TrelloAPIError
from apps.navigation import TIP_MAIN_NAV, TIP_SIDEBAR_NAV_GROUPS
from apps.settings.services import (
    build_settings_overview,
    update_openai,
    update_workspace,
)


class SettingsOverviewView(APIView):
    """Application settings — workspace, Trello and OpenAI configuration."""

    def get(self, request):
        return Response(build_settings_overview())


class WorkspaceSettingsView(APIView):
    """GET/PATCH workspace name."""

    def get(self, request):
        overview = build_settings_overview()
        return Response(overview["sections"]["workspace"])

    def patch(self, request):
        workspace_name = request.data.get("workspace_name", "")
        if not str(workspace_name).strip():
            return Response(
                {"status": "error", "error": "workspace_name is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        update_workspace(workspace_name=str(workspace_name))
        overview = build_settings_overview()
        return Response(overview["sections"]["workspace"])


class TrelloSettingsView(APIView):
    """GET status / POST save Trello credentials (delegates to integration engine)."""

    def get(self, request):
        overview = build_settings_overview()
        return Response(overview["sections"]["trello"])

    def post(self, request):
        data = request.data
        api_key = (data.get("api_key") or "").strip()
        api_token = (data.get("api_token") or data.get("token") or "").strip()
        board_id = (data.get("board_id") or "").strip()
        workspace_id = (data.get("workspace_id") or "").strip()
        name = (data.get("name") or "").strip()

        if not api_key or not api_token:
            return Response(
                {"status": "error", "error": "api_key and api_token are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            client = TrelloClient(api_key=api_key, api_token=api_token)
            member = client.get_member()
            board = client.get_board(board_id) if board_id else None
        except TrelloAPIError as exc:
            return Response(
                {"status": "error", "error": str(exc)},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        connection, created = save_trello_connection(
            api_key=client.api_key,
            api_token=client.api_token,
            member=member,
            board_id=board_id,
            workspace_id=workspace_id,
            name=name,
            board=board,
        )

        overview = build_settings_overview()
        trello = overview["sections"]["trello"]
        trello["created"] = created
        trello["connection_id"] = str(connection.pk)
        return Response(
            trello,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class OpenAISettingsView(APIView):
    """GET/PATCH OpenAI configuration."""

    def get(self, request):
        overview = build_settings_overview()
        return Response(overview["sections"]["openai"])

    def patch(self, request):
        api_key = request.data.get("api_key")
        model = request.data.get("model")

        if api_key is None and model is None:
            return Response(
                {"status": "error", "error": "Provide api_key and/or model"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            update_openai(
                api_key=str(api_key) if api_key is not None else None,
                model=str(model) if model is not None else None,
            )
        except ValueError as exc:
            return Response(
                {"status": "error", "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        overview = build_settings_overview()
        return Response(overview["sections"]["openai"])


class NavigationView(APIView):
    """Server-driven navigation menu for TIP frontend."""

    def get(self, request):
        return Response({"items": TIP_MAIN_NAV, "groups": TIP_SIDEBAR_NAV_GROUPS})
