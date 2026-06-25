from __future__ import annotations

import logging
from typing import Any

from django.utils import timezone

from apps.intelligence.models import ActionExecutionLog, DecisionRecord

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


def enqueue_decision(decision: dict[str, Any]) -> DecisionRecord:
    """Persist decision to action queue."""
    return DecisionRecord.objects.create(
        decision_id=decision["id"],
        source_trace_id=decision.get("source_trace_id", ""),
        board_id=decision.get("board_id", ""),
        insight=decision.get("insight", "")[:5000],
        priority=decision.get("priority", "MEDIUM"),
        recommended_actions=decision.get("recommended_actions", []),
        status=decision.get("status", "OPEN"),
        owner=decision.get("owner", "system"),
        context_json=decision.get("context", {}),
        execution_history=decision.get("execution_history", []),
        score=decision.get("score", 0),
        retry_count=0,
    )


def get_pending_queue(*, board_id: str = "", limit: int = 50) -> list[dict[str, Any]]:
    qs = DecisionRecord.objects.filter(status__in=["OPEN", "PENDING_APPROVAL", "IN_PROGRESS"])
    if board_id:
        qs = qs.filter(board_id=board_id)
    return [_record_to_dict(r) for r in qs.order_by("-score", "-created_at")[:limit]]


def mark_in_progress(decision_id: str) -> None:
    DecisionRecord.objects.filter(decision_id=decision_id).update(status="IN_PROGRESS")


def mark_executed(decision_id: str, history_entry: dict[str, Any]) -> None:
    record = DecisionRecord.objects.filter(decision_id=decision_id).first()
    if not record:
        return
    history = list(record.execution_history or [])
    history.append(history_entry)
    record.execution_history = history
    record.status = "EXECUTED"
    record.save(update_fields=["execution_history", "status", "updated_at"])


def mark_rejected(decision_id: str, reason: str, *, rejected_by: str = "operator") -> None:
    record = DecisionRecord.objects.filter(decision_id=decision_id).first()
    if not record:
        return
    history = list(record.execution_history or [])
    history.append({
        "rejected_by": rejected_by,
        "reason": reason,
        "at": timezone.now().isoformat(),
    })
    record.execution_history = history
    record.status = "REJECTED"
    record.save(update_fields=["execution_history", "status", "updated_at"])


def mark_failed(decision_id: str, error: str, *, retry: bool = True) -> dict[str, Any]:
    record = DecisionRecord.objects.filter(decision_id=decision_id).first()
    if not record:
        return {"status": "not_found"}

    record.retry_count += 1
    history = list(record.execution_history or [])
    history.append({"error": error, "retry_count": record.retry_count, "at": timezone.now().isoformat()})
    record.execution_history = history

    if retry and record.retry_count < MAX_RETRIES:
        record.status = "OPEN"
        record.save(update_fields=["retry_count", "execution_history", "status", "updated_at"])
        return {"status": "retry_scheduled", "retry_count": record.retry_count}

    record.status = "DEAD_LETTER"
    record.save(update_fields=["retry_count", "execution_history", "status", "updated_at"])
    return {"status": "dead_letter", "retry_count": record.retry_count}


def load_decision(decision_id: str) -> dict[str, Any] | None:
    record = DecisionRecord.objects.filter(decision_id=decision_id).first()
    return _record_to_dict(record) if record else None


def _record_to_dict(record: DecisionRecord) -> dict[str, Any]:
    return {
        "id": record.decision_id,
        "decision_id": record.decision_id,
        "source_trace_id": record.source_trace_id,
        "board_id": record.board_id,
        "insight": record.insight,
        "priority": record.priority,
        "recommended_actions": record.recommended_actions,
        "status": record.status,
        "owner": record.owner,
        "context": record.context_json,
        "execution_history": record.execution_history,
        "score": record.score,
        "retry_count": record.retry_count,
        "created_at": record.created_at.isoformat(),
    }
