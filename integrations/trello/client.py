import logging
from typing import Any
from urllib.parse import urljoin

import requests
from django.conf import settings

from integrations.trello.exceptions import TrelloAPIError

logger = logging.getLogger(__name__)

BOARD_FIELDS = "name,desc,url,closed,dateLastActivity"
LIST_FIELDS = "name,pos,closed"
CARD_FIELDS = (
    "name,desc,idList,idBoard,idMembers,due,dueComplete,closed,labels,"
    "dateLastActivity,pos,url,shortUrl,idChecklists,badges"
)
MEMBER_FIELDS = "username,fullName"
ACTION_FIELDS = "type,date,idMemberCreator,data"
ACTIONS_PAGE_SIZE = 1000


class TrelloClient:
    BASE_URL = "https://api.trello.com/1/"

    def __init__(self, api_key: str | None = None, api_token: str | None = None):
        self.api_key = api_key or settings.TRELLO_API_KEY
        self.api_token = api_token or settings.TRELLO_API_TOKEN
        if not self.api_key or not self.api_token:
            raise TrelloAPIError("TRELLO_API_KEY and TRELLO_API_TOKEN must be configured")

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

    def _post(self, path: str, params: dict[str, Any] | None = None) -> Any:
        request_params = {**self._auth_params(), **(params or {})}
        url = urljoin(self.BASE_URL, path.lstrip("/"))
        try:
            response = requests.post(url, params=request_params, timeout=30)
        except requests.RequestException as exc:
            raise TrelloAPIError(f"Trello request failed: {exc}") from exc
        if response.status_code >= 400:
            raise TrelloAPIError(f"Trello API error {response.status_code}: {response.text[:500]}")
        return response.json()

    def _put(self, path: str, params: dict[str, Any] | None = None) -> Any:
        request_params = {**self._auth_params(), **(params or {})}
        url = urljoin(self.BASE_URL, path.lstrip("/"))
        try:
            response = requests.put(url, params=request_params, timeout=30)
        except requests.RequestException as exc:
            raise TrelloAPIError(f"Trello request failed: {exc}") from exc
        if response.status_code >= 400:
            raise TrelloAPIError(f"Trello API error {response.status_code}: {response.text[:500]}")
        return response.json()

    def update_card(self, card_id: str, **fields: Any) -> dict[str, Any]:
        return self._put(f"cards/{card_id}", params=fields)

    def add_member_to_card(self, card_id: str, member_id: str) -> dict[str, Any]:
        return self._post(f"cards/{card_id}/idMembers", params={"value": member_id})

    def add_comment(self, card_id: str, text: str) -> dict[str, Any]:
        return self._post(f"cards/{card_id}/actions/comments", params={"text": text})

    def get_board(self, board_id: str) -> dict[str, Any]:
        return self._get(
            f"boards/{board_id}",
            params={"fields": BOARD_FIELDS},
        )

    def get_board_lists(self, board_id: str) -> list[dict[str, Any]]:
        return self._get(
            f"boards/{board_id}/lists",
            params={"fields": LIST_FIELDS},
        )

    def get_board_cards(self, board_id: str) -> list[dict[str, Any]]:
        return self._get(
            f"boards/{board_id}/cards",
            params={"fields": CARD_FIELDS},
        )

    def get_board_members(self, board_id: str) -> list[dict[str, Any]]:
        return self._get(
            f"boards/{board_id}/members",
            params={"fields": MEMBER_FIELDS},
        )

    def get_board_actions(self, board_id: str) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        before: str | None = None

        while True:
            params: dict[str, Any] = {
                "filter": "all",
                "limit": ACTIONS_PAGE_SIZE,
                "fields": ACTION_FIELDS,
            }
            if before:
                params["before"] = before

            page = self._get(f"boards/{board_id}/actions", params=params)
            if not page:
                break

            actions.extend(page)

            if len(page) < ACTIONS_PAGE_SIZE:
                break

            before = page[-1]["id"]
            logger.info("Fetched %d Trello actions for board %s", len(actions), board_id)

        return actions
