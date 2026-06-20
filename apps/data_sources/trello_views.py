from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.integrations.core.engine import SyncEngine
from apps.integrations.core.exceptions import (
    AuthenticationError,
    ConnectionNotFoundError,
    IntegrationError,
)
from apps.integrations.trello.client import TrelloClient
from apps.integrations.trello.connections import (
    resolve_trello_connection,
    save_trello_connection,
    status_payload,
)
from apps.integrations.trello.exceptions import TrelloAPIError


class DataSourceTrelloConnectView(APIView):
    """
    POST /api/v1/data-sources/trello/connect/

    Body: api_key, api_token
    Optional: board_id, workspace_id, name
    """

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
            if board_id and board:
                board_workspace = board.get("idOrganization") or ""
                if workspace_id and board_workspace and board_workspace != workspace_id:
                    return Response(
                        {
                            "status": "error",
                            "error": (
                                f"Board {board_id} belongs to workspace {board_workspace}, "
                                f"not {workspace_id}"
                            ),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
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

        payload = status_payload(connection)
        payload["created"] = created
        if board:
            payload["board"] = {
                "id": board.get("id"),
                "name": board.get("name"),
                "url": board.get("url"),
            }

        return Response(
            payload,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class DataSourceTrelloSyncView(APIView):
    """
    POST /api/v1/data-sources/trello/sync/

    Body (optional): connection_id, board_id
    """

    def post(self, request):
        data = request.data or {}
        connection_id = data.get("connection_id")
        board_id = data.get("board_id")

        try:
            connection = resolve_trello_connection(
                connection_id=str(connection_id) if connection_id else None,
                board_id=board_id,
            )
            result = SyncEngine().run("trello", str(connection.pk))
        except ConnectionNotFoundError as exc:
            return Response(
                {"status": "error", "error": str(exc)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except AuthenticationError as exc:
            return Response(
                {"status": "error", "error": str(exc)},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except IntegrationError as exc:
            return Response(
                {"status": "error", "error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        response = {
            "status": "success",
            **result.as_dict(),
        }
        return Response(response, status=status.HTTP_200_OK)


class DataSourceTrelloStatusView(APIView):
    """
    GET /api/v1/data-sources/trello/status/

    Query (optional): connection_id, board_id
    """

    def get(self, request):
        connection_id = request.query_params.get("connection_id")
        board_id = request.query_params.get("board_id")

        try:
            if connection_id or board_id:
                connection = resolve_trello_connection(
                    connection_id=connection_id,
                    board_id=board_id,
                )
            else:
                from apps.integrations.trello.connections import get_account_connection

                connection = get_account_connection()
                if not connection:
                    connection = resolve_trello_connection()
        except ConnectionNotFoundError:
            return Response(
                {
                    "status": "disconnected",
                    "provider": "trello",
                    "connection_id": None,
                    "credentials_configured": False,
                    "last_synced_at": None,
                    "tasks_count": 0,
                },
                status=status.HTTP_200_OK,
            )

        return Response(status_payload(connection))
