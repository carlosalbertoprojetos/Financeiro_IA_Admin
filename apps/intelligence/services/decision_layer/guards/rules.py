from __future__ import annotations

import os
from typing import Any

DESTRUCTIVE_ACTIONS = frozenset({"REOPEN_CARD", "MOVE_CARD", "ADJUST_PRIORITY"})
BULK_THRESHOLD = 5
APPROVAL_REQUIRED_ACTIONS = frozenset({"REOPEN_CARD", "MOVE_CARD", "ADJUST_PRIORITY", "REASSIGN_OWNER"})


def is_auto_execution_enabled() -> bool:
    return os.environ.get("DAL_AUTO_EXECUTION", "false").lower() in ("true", "1", "yes")


def max_auto_actions_per_hour() -> int:
    try:
        return int(os.environ.get("DAL_MAX_AUTO_ACTIONS_PER_HOUR", "10"))
    except ValueError:
        return 10


def action_cooldown_seconds() -> int:
    try:
        return int(os.environ.get("DAL_ACTION_COOLDOWN_SECONDS", "300"))
    except ValueError:
        return 300


def validate_action(
    action: dict[str, Any],
    *,
    recent_executions: list[dict[str, Any]] | None = None,
    auto_count_last_hour: int = 0,
    bulk_card_count: int = 1,
) -> dict[str, Any]:
    """
    Safety guardrails before action execution.
    Returns {allowed, requires_approval, reason, blocked_by}.
    """
    action_type = action.get("action_type", "")
    execution_mode = action.get("execution_mode", "MANUAL")
    recent = recent_executions or []

    if bulk_card_count > BULK_THRESHOLD:
        return {
            "allowed": False,
            "requires_approval": True,
            "reason": f"Bulk action affects {bulk_card_count} cards (limit {BULK_THRESHOLD})",
            "blocked_by": "bulk_limit",
        }

    if action_type in DESTRUCTIVE_ACTIONS:
        return {
            "allowed": execution_mode != "AUTOMATIC",
            "requires_approval": True,
            "reason": f"Destructive action {action_type} requires human approval",
            "blocked_by": "destructive_guard",
        }

    if action_type in APPROVAL_REQUIRED_ACTIONS and execution_mode == "AUTOMATIC":
        return {
            "allowed": False,
            "requires_approval": True,
            "reason": f"{action_type} cannot run in AUTOMATIC mode",
            "blocked_by": "approval_required",
        }

    if execution_mode == "AUTOMATIC":
        if not is_auto_execution_enabled():
            return {
                "allowed": False,
                "requires_approval": True,
                "reason": "Auto execution disabled (DAL_AUTO_EXECUTION=false)",
                "blocked_by": "auto_disabled",
            }
        if auto_count_last_hour >= max_auto_actions_per_hour():
            return {
                "allowed": False,
                "requires_approval": True,
                "reason": f"Hourly auto-action limit reached ({max_auto_actions_per_hour()})",
                "blocked_by": "rate_limit",
            }

    target = action.get("target_card_id") or action.get("params", {}).get("card_id", "")
    if target and _is_loop(recent, action_type, target):
        return {
            "allowed": False,
            "requires_approval": True,
            "reason": f"Loop detected: {action_type} on {target} within cooldown",
            "blocked_by": "loop_guard",
        }

    return {"allowed": True, "requires_approval": execution_mode == "SEMI_AUTOMATIC", "reason": "", "blocked_by": ""}


def _is_loop(recent: list[dict[str, Any]], action_type: str, card_id: str) -> bool:
    for entry in recent:
        if entry.get("action_type") == action_type and entry.get("target_card_id") == card_id:
            if entry.get("within_cooldown"):
                return True
    return False
