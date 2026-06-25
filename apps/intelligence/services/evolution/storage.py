from __future__ import annotations

import logging
from typing import Any

from apps.intelligence.models import EvolutionLog

logger = logging.getLogger(__name__)


def log_evolution_event(
    *,
    version_from: str,
    version_to: str,
    change_type: str,
    affected_layers: list[str],
    risk_assessment: dict[str, Any],
    status: str = "pending",
    details: dict[str, Any] | None = None,
) -> EvolutionLog | None:
    try:
        return EvolutionLog.objects.create(
            version_from=version_from,
            version_to=version_to,
            change_type=change_type,
            affected_layers=affected_layers,
            risk_assessment=risk_assessment,
            status=status,
            details_json=details or {},
        )
    except Exception:
        logger.exception("Failed to log evolution event")
        return None


def get_evolution_history(*, limit: int = 50) -> list[dict[str, Any]]:
    rows = EvolutionLog.objects.order_by("-created_at")[:limit]
    return [
        {
            "id": r.id,
            "version_from": r.version_from,
            "version_to": r.version_to,
            "change_type": r.change_type,
            "affected_layers": r.affected_layers,
            "risk_assessment": r.risk_assessment,
            "status": r.status,
            "timestamp": r.created_at.isoformat(),
        }
        for r in rows
    ]
