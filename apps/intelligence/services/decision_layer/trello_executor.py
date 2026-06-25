from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class TrelloActionExecutor:
    """Execute actions against Trello API."""

    def __init__(self, *, dry_run: bool = False) -> None:
        self.dry_run = dry_run
        self._client = None

    def _get_client(self):
        if self._client is None:
            from integrations.trello.client import TrelloClient
            self._client = TrelloClient()
        return self._client

    def execute(self, action: dict[str, Any]) -> dict[str, Any]:
        action_type = action.get("action_type", "")
        card_id = action.get("target_card_id", "")
        params = action.get("params") or {}

        if self.dry_run:
            return {
                "provider": "trello",
                "dry_run": True,
                "action_type": action_type,
                "target_card_id": card_id,
                "would_execute": True,
            }

        client = self._get_client()

        if action_type == "ADD_COMMENT":
            text = params.get("text", "Action triggered by EOR Decision Layer")
            result = client.add_comment(card_id, text)
            return {"provider": "trello", "action": "add_comment", "result": result, "target_card_id": card_id}

        if action_type == "REOPEN_CARD":
            result = client.update_card(card_id, closed=False)
            return {"provider": "trello", "action": "reopen", "result": result, "target_card_id": card_id}

        if action_type == "ADJUST_PRIORITY":
            pos = params.get("pos", "top")
            result = client.update_card(card_id, pos=pos)
            return {"provider": "trello", "action": "adjust_priority", "result": result, "target_card_id": card_id}

        if action_type == "REASSIGN_OWNER":
            member_id = params.get("member_id", "")
            if member_id:
                result = client.add_member_to_card(card_id, member_id)
                return {"provider": "trello", "action": "reassign", "result": result, "target_card_id": card_id}
            return {"provider": "trello", "action": "reassign", "status": "suggested", "target_card_id": card_id}

        if action_type == "MOVE_CARD":
            list_id = params.get("list_id", "")
            if list_id:
                result = client.update_card(card_id, idList=list_id)
                return {"provider": "trello", "action": "move", "result": result, "target_card_id": card_id}
            raise ValueError("MOVE_CARD requires list_id in params")

        if action_type == "ESCALATE_TASK":
            text = params.get("text", f"[EOR ESCALATION] {params.get('reason', 'Critical item')}")
            comment = client.add_comment(card_id, text)
            priority = client.update_card(card_id, pos="top")
            return {
                "provider": "trello",
                "action": "escalate",
                "comment": comment,
                "priority": priority,
                "target_card_id": card_id,
            }

        raise ValueError(f"Unsupported Trello action: {action_type}")
