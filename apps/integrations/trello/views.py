from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.integrations.core.engine import SyncEngine
from apps.integrations.core.exceptions import (
    AuthenticationError,
    ConnectionNotFoundError,
    IntegrationError,
)
from apps.integrations.models import IntegrationConnection
from apps.integrations.trello.adapter import resolve_credentials
from apps.integrations.trello.connections import save_trello_connection, status_payload
from apps.integrations.trello.client import TrelloClient
from apps.integrations.trello.exceptions import TrelloAPIError


def _connection_payload(connection: IntegrationConnection) -> dict[str, Any]:
    payload = status_payload(connection)
    payload.pop("status", None)
    payload.pop("is_account_connection", None)
    payload.pop("tasks_count", None)
    payload.pop("credentials_configured", None)
    return payload


def _board_payload(board: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": board.get("id"),
        "name": board.get("name"),
        "url": board.get("url"),
        "workspace_id": board.get("idOrganization") or "",
        "closed": bool(board.get("closed")),
    }


def _workspace_payload(org: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": org.get("id"),
        "name": org.get("displayName") or org.get("name") or "",
        "url": org.get("url") or "",
    }


class TrelloConnectView(APIView):
    """
    Authenticate Trello credentials and register a board connection.

    POST body:
      - api_key (required unless env default)
      - api_token (required unless env default)
      - board_id (required) — Trello board to sync
      - workspace_id (optional) — Trello organization scope
      - name (optional) — friendly label for the connection
    """

    def post(self, request):
        data = request.data
        api_key = data.get("api_key") or ""
        api_token = data.get("api_token") or ""
        board_id = (data.get("board_id") or "").strip()
        workspace_id = (data.get("workspace_id") or "").strip()
        name = (data.get("name") or "").strip()

        if not board_id:
            return Response(
                {"error": "board_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            client = TrelloClient(api_key=api_key or None, api_token=api_token or None)
            member = client.get_member()
            board = client.get_board(board_id)
            workspaces = client.get_workspaces()
        except TrelloAPIError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        board_workspace = board.get("idOrganization") or ""
        if workspace_id and board_workspace and board_workspace != workspace_id:
            return Response(
                {
                    "error": (
                        f"Board {board_id} belongs to workspace {board_workspace}, "
                        f"not {workspace_id}"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        resolved_workspace = workspace_id or board_workspace
        resolved_name = name or board.get("name") or board_id

        connection, created = save_trello_connection(
            api_key=client.api_key,
            api_token=client.api_token,
            member=member,
            board_id=board_id,
            workspace_id=resolved_workspace,
            name=resolved_name,
            board=board,
        )

        return Response(
            {
                "connection": _connection_payload(connection),
                "created": created,
                "board": _board_payload(board),
                "member": {
                    "id": member.get("id"),
                    "username": member.get("username"),
                    "full_name": member.get("fullName"),
                },
                "workspaces": [_workspace_payload(org) for org in workspaces],
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class TrelloWorkspacesView(APIView):
    """List workspaces for an existing Trello connection."""

    def get(self, request, connection_id: str):
        connection = _load_connection(connection_id)
        if isinstance(connection, Response):
            return connection

        try:
            api_key, api_token = resolve_credentials(connection)
            client = TrelloClient(api_key=api_key, api_token=api_token)
            workspaces = client.get_workspaces()
        except (AuthenticationError, TrelloAPIError) as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(
            {
                "connection_id": str(connection.pk),
                "workspaces": [_workspace_payload(org) for org in workspaces],
            }
        )


class TrelloBoardsView(APIView):
    """List boards for a connection, optionally filtered by workspace."""

    def get(self, request, connection_id: str):
        connection = _load_connection(connection_id)
        if isinstance(connection, Response):
            return connection

        workspace_id = (request.query_params.get("workspace_id") or connection.workspace_id or "").strip()

        try:
            api_key, api_token = resolve_credentials(connection)
            client = TrelloClient(api_key=api_key, api_token=api_token)
            boards = client.get_boards(workspace_id=workspace_id or None)
        except (AuthenticationError, TrelloAPIError) as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(
            {
                "connection_id": str(connection.pk),
                "workspace_id": workspace_id,
                "boards": [_board_payload(board) for board in boards],
            }
        )


class TrelloSyncView(APIView):
    """Run Integration Engine sync for a Trello connection."""

    def post(self, request, connection_id: str):
        try:
            result = SyncEngine().run("trello", connection_id)
        except ConnectionNotFoundError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except AuthenticationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        except IntegrationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(result.as_dict(), status=status.HTTP_200_OK)


def _load_connection(connection_id: str) -> IntegrationConnection | Response:
    try:
        return IntegrationConnection.objects.get(
            pk=connection_id,
            provider=IntegrationConnection.Provider.TRELLO,
        )
    except IntegrationConnection.DoesNotExist:
        return Response(
            {"error": f"Trello connection not found: {connection_id}"},
            status=status.HTTP_404_NOT_FOUND,
        )
