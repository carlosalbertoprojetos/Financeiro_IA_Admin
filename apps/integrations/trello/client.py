import logging
from typing import Any
from urllib.parse import urljoin

import requests
from django.conf import settings

from apps.integrations.trello.exceptions import TrelloAPIError

logger = logging.getLogger(__name__)

BOARD_FIELDS = "id,name,desc,url,closed,idOrganization,dateLastActivity"
LIST_FIELDS = "id,name,pos,closed,idBoard"
CARD_FIELDS = (
    "id,name,desc,idList,idBoard,due,dueComplete,closed,labels,"
    "dateLastActivity,url,shortUrl,pos"
)
ORGANIZATION_FIELDS = "id,name,displayName,url"
MEMBER_FIELDS = "id,username,fullName"


class TrelloClient:
    """HTTP client for the Trello REST API (API Key + Token)."""

    BASE_URL = "https://api.trello.com/1/"

    def __init__(self, api_key: str | None = None, api_token: str | None = None) -> None:
        self.api_key = api_key or settings.TRELLO_API_KEY
        self.api_token = api_token or settings.TRELLO_API_TOKEN
        if not self.api_key or not self.api_token:
            raise TrelloAPIError("api_key and api_token are required")

    def _auth_params(self) -> dict[str, str]:
        return {"key": self.api_key, "token": self.api_token}

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        request_params = {**self._auth_params(), **(params or {})}
        url = urljoin(self.BASE_URL, path.lstrip("/"))

        try:
            response = requests.get(url, params=request_params, timeout=30)
        except requests.RequestException as exc:
            raise TrelloAPIError(f"Trello request failed: {exc}") from exc

        if response.status_code >= 400:
            raise TrelloAPIError(
                f"Trello API error {response.status_code}: {response.text[:500]}"
            )

        return response.json()

    def get_member(self) -> dict[str, Any]:
        """Validate credentials and return the authenticated member."""
        return self._get("members/me", params={"fields": MEMBER_FIELDS})

    def get_workspaces(self) -> list[dict[str, Any]]:
        """List Trello organizations (workspaces) for the authenticated member."""
        return self._get(
            "members/me/organizations",
            params={"fields": ORGANIZATION_FIELDS},
        )

    def get_boards(self, workspace_id: str | None = None) -> list[dict[str, Any]]:
        """
        List boards accessible to the member.

        When workspace_id is set, returns boards belonging to that workspace.
        """
        if workspace_id:
            return self._get(
                f"organizations/{workspace_id}/boards",
                params={"fields": BOARD_FIELDS, "filter": "open"},
            )

        return self._get(
            "members/me/boards",
            params={"fields": BOARD_FIELDS, "filter": "open"},
        )

    def get_board(self, board_id: str) -> dict[str, Any]:
        return self._get(f"boards/{board_id}", params={"fields": BOARD_FIELDS})

    def get_lists(self, board_id: str) -> list[dict[str, Any]]:
        return self._get(
            f"boards/{board_id}/lists",
            params={"fields": LIST_FIELDS, "filter": "open"},
        )

    def get_cards(self, board_id: str) -> list[dict[str, Any]]:
        return self._get(
            f"boards/{board_id}/cards",
            params={"fields": CARD_FIELDS},
        )
