from __future__ import annotations

import os
from datetime import timedelta
from typing import Any

from django.utils import timezone

from apps.intelligence.models import PilotConfig
from apps.intelligence.services.decision_layer.guards.rules import is_auto_execution_enabled
from integrations.trello.models import Board


class PilotConfigurationError(Exception):
    pass


MIN_PILOT_DAYS = 5
MAX_PILOT_DAYS = 10


def ensure_human_in_loop() -> None:
    """POCL requires human approval for every action."""
    if is_auto_execution_enabled():
        raise PilotConfigurationError(
            "DAL_AUTO_EXECUTION must be false during operational pilot. "
            "Set DAL_AUTO_EXECUTION=false in environment."
        )


def validate_pilot_scope(*, board_id: str, team_name: str, duration_days: int) -> Board:
    """Validate POCL real-world scope: one active board, one real team, 5-10 days."""
    if not board_id.strip():
        raise PilotConfigurationError("POCL requires one active board_id.")
    if not team_name.strip():
        raise PilotConfigurationError("POCL requires one real operational team_name.")
    if duration_days < MIN_PILOT_DAYS or duration_days > MAX_PILOT_DAYS:
        raise PilotConfigurationError(
            f"POCL duration must be between {MIN_PILOT_DAYS} and {MAX_PILOT_DAYS} days."
        )

    board = Board.objects.filter(trello_id=board_id).first()
    if not board:
        raise PilotConfigurationError(
            "POCL board must exist in the local Trello projection. "
            "Run a real Trello sync before activating the pilot."
        )
    if board.closed:
        raise PilotConfigurationError("POCL board must be active, not closed.")
    return board


def get_active_pilot(*, board_id: str = "") -> PilotConfig | None:
    qs = PilotConfig.objects.filter(status=PilotConfig.Status.ACTIVE)
    if board_id:
        qs = qs.filter(board_id=board_id)
    pilot = qs.order_by("-started_at").first()
    if pilot:
        return pilot
    env_board = os.environ.get("POCL_BOARD_ID", "").strip()
    if env_board and (not board_id or board_id == env_board):
        if os.environ.get("POCL_ACTIVE", "false").lower() in ("true", "1", "yes"):
            return PilotConfig.objects.filter(board_id=env_board).order_by("-created_at").first()
    return None


def is_pilot_board(board_id: str) -> bool:
    return get_active_pilot(board_id=board_id) is not None


def activate_pilot(
    *,
    board_id: str,
    team_name: str,
    board_name: str = "",
    duration_days: int = 10,
    config: dict[str, Any] | None = None,
) -> PilotConfig:
    ensure_human_in_loop()
    board = validate_pilot_scope(
        board_id=board_id,
        team_name=team_name,
        duration_days=duration_days,
    )
    PilotConfig.objects.filter(board_id=board_id, status=PilotConfig.Status.ACTIVE).update(
        status=PilotConfig.Status.COMPLETED,
    )
    now = timezone.now()
    return PilotConfig.objects.create(
        board_id=board_id,
        board_name=board_name or board.name,
        team_name=team_name,
        status=PilotConfig.Status.ACTIVE,
        started_at=now,
        ends_at=now + timedelta(days=duration_days),
        config_json={
            "human_in_the_loop": True,
            "auto_execution": False,
            "duration_days": duration_days,
            "real_mode": True,
            "observed_impact_only": True,
            "board_last_synced_at": board.last_synced_at.isoformat() if board.last_synced_at else "",
            **(config or {}),
        },
    )


def pilot_status_summary(*, board_id: str = "") -> dict[str, Any]:
    pilot = get_active_pilot(board_id=board_id)
    if not pilot:
        return {"active": False, "human_in_the_loop": not is_auto_execution_enabled()}
    return {
        "active": True,
        "pilot_id": pilot.id,
        "board_id": pilot.board_id,
        "board_name": pilot.board_name,
        "team_name": pilot.team_name,
        "started_at": pilot.started_at.isoformat() if pilot.started_at else "",
        "ends_at": pilot.ends_at.isoformat() if pilot.ends_at else "",
        "human_in_the_loop": True,
        "auto_execution": is_auto_execution_enabled(),
    }
