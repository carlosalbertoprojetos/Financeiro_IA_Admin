from typing import Any

from django.conf import settings
from django.utils import timezone

from apps.integrations.core.adapter import BaseIntegrationAdapter, IncrementalFetchResult
from apps.integrations.core.canonical import CanonicalTask
from apps.integrations.core.credentials import decrypt_credentials
from apps.integrations.core.exceptions import AuthenticationError
from apps.integrations.core.ingestion_state import IngestionCursor
from apps.integrations.core.registry import registry
from apps.integrations.models import IntegrationConnection
from apps.integrations.trello.client import TrelloClient
from apps.integrations.trello.exceptions import TrelloAPIError
from apps.integrations.trello.incremental import (
    IncrementalCursorSnapshot,
    build_next_cursor,
    filter_changed_cards,
)
from apps.integrations.trello.mapper import map_trello_payload


def resolve_credentials(connection: IntegrationConnection) -> tuple[str, str]:
    creds = decrypt_credentials(connection.credentials or {})
    api_key = creds.get("api_key") or settings.TRELLO_API_KEY
    api_token = creds.get("api_token") or settings.TRELLO_API_TOKEN
    if not api_key or not api_token:
        raise AuthenticationError("Trello api_key and api_token are required on the connection")
    return api_key, api_token


@registry.register
class TrelloAdapter(BaseIntegrationAdapter):
    """
    Trello provider adapter.

    Mapping: board → project, card → task, list → status.
    Supports multiple workspaces via IntegrationConnection.workspace_id.
    """

    provider = "trello"

    def __init__(self) -> None:
        self._client: TrelloClient | None = None
        self.last_sync_details: dict[str, Any] = {}

    def authenticate(self, connection: IntegrationConnection) -> None:
        api_key, api_token = resolve_credentials(connection)
        try:
            self._client = TrelloClient(api_key=api_key, api_token=api_token)
            board = self._client.get_board(connection.project_id)
            if connection.workspace_id:
                board_workspace = board.get("idOrganization") or ""
                if board_workspace and board_workspace != connection.workspace_id:
                    raise AuthenticationError(
                        f"Board {connection.project_id} does not belong to workspace "
                        f"{connection.workspace_id}"
                    )
        except TrelloAPIError as exc:
            raise AuthenticationError(str(exc)) from exc

    def fetch(self, connection: IntegrationConnection) -> dict[str, Any]:
        if self._client is None:
            self.authenticate(connection)

        assert self._client is not None
        board_id = connection.project_id
        board = self._client.get_board(board_id)
        lists = self._client.get_lists(board_id)
        cards = self._client.get_cards(board_id)

        return {
            "board": board,
            "lists": lists,
            "cards": cards,
            "workspace_id": connection.workspace_id or board.get("idOrganization") or "",
        }

    def map(self, raw_payload: dict[str, Any], connection: IntegrationConnection) -> list[CanonicalTask]:
        workspace_id = raw_payload.get("workspace_id") or connection.workspace_id or ""
        return map_trello_payload(raw_payload, workspace_id=workspace_id)

    def fetch_incremental(
        self,
        state: IngestionCursor,
        connection: IntegrationConnection,
    ) -> IncrementalFetchResult:
        """
        Fetch board changes since last_sync_cursor.

        Detects created cards, updated cards (dateLastActivity) and list moves
        (idList diff vs stored card_list_map). Trello has no native cursor API;
        changes are simulated client-side via updated_since.
        """
        if self._client is None:
            self.authenticate(connection)

        assert self._client is not None
        board_id = connection.project_id
        board = self._client.get_board(board_id)
        lists = self._client.get_lists(board_id)
        all_cards = self._client.get_cards(board_id)

        snapshot = IncrementalCursorSnapshot.from_state(state)
        changed_cards, change_stats, mode = filter_changed_cards(
            all_cards,
            snapshot=snapshot,
        )

        synced_at = timezone.now().isoformat()
        payload = {
            "board": board,
            "lists": lists,
            "cards": changed_cards,
            "workspace_id": connection.workspace_id or board.get("idOrganization") or "",
            "incremental": {
                "mode": mode,
                "updated_since": (
                    snapshot.updated_since.isoformat() if snapshot.updated_since else None
                ),
                "changes": change_stats.as_dict(),
            },
        }

        next_cursor = build_next_cursor(
            board_id=board_id,
            all_cards=all_cards,
            synced_at=synced_at,
            mode=mode,
            change_stats=change_stats,
        )

        self.last_sync_details = {
            "board_id": board.get("id"),
            "board_name": board.get("name"),
            "mode": mode,
            "cards_total": len(all_cards),
            "cards_fetched": len(changed_cards),
            **change_stats.as_dict(),
        }

        return IncrementalFetchResult(
            payload=payload,
            cursor=next_cursor,
            complete=True,
            fetched_count=len(changed_cards),
        )

    def sync(self, connection: IntegrationConnection) -> list[CanonicalTask]:
        """Fetch live Trello data and return canonical tasks."""
        self.authenticate(connection)
        raw_payload = self.fetch(connection)
        tasks = self.map(raw_payload, connection)

        board = raw_payload["board"]
        self.last_sync_details = {
            "board_id": board.get("id"),
            "board_name": board.get("name"),
            "workspace_id": raw_payload.get("workspace_id") or "",
            "lists": len(raw_payload.get("lists", [])),
            "cards": len(raw_payload.get("cards", [])),
            "tasks_mapped": len(tasks),
        }
        return tasks
