from __future__ import annotations

import logging
from typing import Any

from apps.intelligence.models import OrganizationalMemory

logger = logging.getLogger(__name__)


def store_organizational_memory(
    *,
    memory_key: str,
    memory_type: str,
    title: str,
    content: str,
    board_id: str = "",
    decision_id: str = "",
    related_action_type: str = "",
    effectiveness_score: float = 0,
    context: dict[str, Any] | None = None,
) -> OrganizationalMemory | None:
    try:
        return OrganizationalMemory.objects.update_or_create(
            memory_key=memory_key,
            defaults={
                "memory_type": memory_type,
                "title": title[:500],
                "content": content[:10000],
                "board_id": board_id,
                "decision_id": decision_id,
                "related_action_type": related_action_type,
                "effectiveness_score": effectiveness_score,
                "context_json": context or {},
            },
        )[0]
    except Exception:
        logger.exception("Failed to store organizational memory")
        return None


def record_lesson_from_effectiveness(record: dict[str, Any]) -> None:
    """Create a lesson_learned memory entry from an effectiveness record."""
    action_type = record.get("action_type", "")
    outcome = record.get("outcome_label", "")
    eff = record.get("effectiveness_score", 0)
    category = record.get("category", "GENERAL")

    if outcome == "SUCCESS" and eff >= 60:
        title = f"{action_type} effective for {category}"
        content = (
            f"Action {action_type} reduced risk from {record.get('risk_before')} "
            f"to {record.get('risk_after')} (effectiveness={eff})."
        )
        memory_type = "lesson_learned"
    elif outcome == "FAILURE":
        title = f"{action_type} ineffective for {category}"
        content = f"Action {action_type} did not improve outcomes (effectiveness={eff})."
        memory_type = "lesson_learned"
    else:
        return

    store_organizational_memory(
        memory_key=f"lesson_{record.get('decision_id', '')}_{action_type}",
        memory_type=memory_type,
        title=title,
        content=content,
        board_id=record.get("board_id", ""),
        decision_id=record.get("decision_id", ""),
        related_action_type=action_type,
        effectiveness_score=eff,
        context={"outcome": outcome, "category": category},
    )

    if outcome == "SUCCESS" and eff >= 70:
        store_organizational_memory(
            memory_key=f"playbook_candidate_{category}_{action_type}".lower(),
            memory_type="playbook_candidate",
            title=f"Playbook candidate: {category} → {action_type}",
            content=content,
            board_id=record.get("board_id", ""),
            related_action_type=action_type,
            effectiveness_score=eff,
            context={
                "category": category,
                "recommended_action": action_type,
                "condition": f"{category} + risco alto" if record.get("risk_before", 0) >= 50 else category,
                "risk_threshold": 50,
            },
        )


def get_memory_history(*, board_id: str = "", limit: int = 50) -> list[dict[str, Any]]:
    qs = OrganizationalMemory.objects.all().order_by("-created_at")
    if board_id:
        qs = qs.filter(board_id=board_id)
    return [
        {
            "memory_key": m.memory_key,
            "memory_type": m.memory_type,
            "title": m.title,
            "content": m.content[:500],
            "board_id": m.board_id,
            "decision_id": m.decision_id,
            "related_action_type": m.related_action_type,
            "effectiveness_score": m.effectiveness_score,
            "created_at": m.created_at.isoformat(),
        }
        for m in qs[:limit]
    ]
