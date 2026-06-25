from __future__ import annotations

from typing import Any

from apps.intelligence.models import OrganizationalMemory, PlaybookRecord
from apps.intelligence.services.organizational_learning.patterns.analyzer import get_action_historical_stats


def generate_playbooks(*, board_id: str = "", min_sample_size: int = 3) -> list[dict[str, Any]]:
    """
    Generate operational playbooks from historical effectiveness data.
    Only includes playbooks backed by real evidence (min sample size).
    """
    memories = OrganizationalMemory.objects.filter(memory_type="playbook_candidate")
    if board_id:
        memories = memories.filter(board_id=board_id)

    playbooks: list[dict[str, Any]] = []
    seen: set[str] = set()

    for mem in memories:
        ctx = mem.context_json or {}
        category = ctx.get("category", "GENERAL")
        condition = ctx.get("condition", "")
        action_type = ctx.get("recommended_action", "")
        key = f"{category}|{condition}|{action_type}"
        if key in seen:
            continue

        stats = get_action_historical_stats(action_type, category=category, board_id=board_id)
        if stats["sample_size"] < min_sample_size:
            continue

        seen.add(key)
        playbook = {
            "id": mem.memory_key,
            "when": {
                "category": category,
                "condition": condition,
                "risk_threshold": ctx.get("risk_threshold"),
            },
            "recommended_action": action_type,
            "historical_effectiveness_pct": stats["success_rate_pct"],
            "avg_risk_reduction_pct": stats["avg_risk_reduction_pct"],
            "sample_size": stats["sample_size"],
            "evidence_based": True,
        }
        playbooks.append(playbook)
        _persist_playbook(playbook, board_id=board_id or mem.board_id)

    if not playbooks:
        playbooks = _playbooks_from_effectiveness_records(board_id, min_sample_size)

    return sorted(playbooks, key=lambda p: p.get("historical_effectiveness_pct") or 0, reverse=True)


def _playbooks_from_effectiveness_records(board_id: str, min_sample_size: int) -> list[dict[str, Any]]:
    from apps.intelligence.models import DecisionEffectivenessRecord
    from django.db.models import Avg, Count, Q
    from apps.intelligence.services.organizational_learning.outcomes.evaluator import OUTCOME_SUCCESS

    qs = DecisionEffectivenessRecord.objects.all()
    if board_id:
        qs = qs.filter(board_id=board_id)

    combos = qs.values("category", "action_type").annotate(
        count=Count("id"),
        success=Count("id", filter=Q(outcome_label=OUTCOME_SUCCESS)),
        avg_eff=Avg("effectiveness_score"),
        avg_risk_before=Avg("risk_before"),
        avg_risk_after=Avg("risk_after"),
    ).filter(count__gte=min_sample_size)

    playbooks = []
    for c in combos:
        risk_red = 0.0
        if c["avg_risk_before"]:
            risk_red = round(((c["avg_risk_before"] - c["avg_risk_after"]) / c["avg_risk_before"]) * 100, 1)
        success_rate = round((c["success"] / c["count"]) * 100, 1)
        condition = _condition_label(c["category"], c["avg_risk_before"] or 0)
        playbook = {
            "id": f"pb_{c['category']}_{c['action_type']}".lower(),
            "when": {"category": c["category"] or "GENERAL", "condition": condition},
            "recommended_action": c["action_type"],
            "historical_effectiveness_pct": success_rate,
            "avg_risk_reduction_pct": risk_red,
            "sample_size": c["count"],
            "evidence_based": True,
        }
        playbooks.append(playbook)
        _persist_playbook(playbook, board_id=board_id)
    return playbooks


def _condition_label(category: str, avg_risk: float) -> str:
    parts = []
    if category and category != "GENERAL":
        parts.append(category)
    if avg_risk >= 50:
        parts.append("risco alto")
    if avg_risk >= 70:
        parts.append("atraso provável")
    return " + ".join(parts) if parts else "operational risk detected"


def _persist_playbook(playbook: dict[str, Any], *, board_id: str = "") -> None:
    try:
        PlaybookRecord.objects.update_or_create(
            playbook_id=playbook["id"],
            defaults={
                "board_id": board_id,
                "category": playbook["when"].get("category", ""),
                "condition_text": playbook["when"].get("condition", ""),
                "recommended_action": playbook["recommended_action"],
                "effectiveness_pct": playbook.get("historical_effectiveness_pct") or 0,
                "sample_size": playbook.get("sample_size", 0),
                "playbook_json": playbook,
            },
        )
    except Exception:
        pass


def find_playbook_for_context(
    *,
    category: str = "",
    risk_score: float = 0,
    board_id: str = "",
) -> dict[str, Any] | None:
    """Match a playbook to current operational context."""
    playbooks = generate_playbooks(board_id=board_id, min_sample_size=2)
    best = None
    best_score = -1.0
    for pb in playbooks:
        when = pb.get("when", {})
        if category and when.get("category", "").upper() != category.upper():
            continue
        threshold = when.get("risk_threshold") or 50
        if risk_score < threshold:
            continue
        eff = pb.get("historical_effectiveness_pct") or 0
        if eff > best_score:
            best_score = eff
            best = pb
    return best
