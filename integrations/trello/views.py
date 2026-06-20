from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from integrations.trello.exceptions import TrelloAPIError
from integrations.trello.services.sync import sync_board


class SyncBoardView(APIView):
    """Trigger ingestion sync for a Trello board."""

    def post(self, request, board_id: str):
        try:
            result = sync_board(board_id)
        except TrelloAPIError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(result.as_dict(), status=status.HTTP_200_OK)
