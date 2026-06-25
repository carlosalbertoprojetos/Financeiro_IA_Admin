from __future__ import annotations

from typing import Any

from django.db.models import Avg, Count

from apps.intelligence.models import DecisionEffectivenessRecord, OrganizationalMemory
from apps.intelligence.services.organizational_learning.outcomes.evaluator import OUTCOME_SUCCESS


def compute_eor_maturity_index(*, board_id: str = "") -> dict[str, Any]:
    """
    Proprietary EOR Maturity Index (0-100) from real operational data.
    Components: SLA, Effectiveness, Risk, Productivity, Learning.
    """
    eff_qs = DecisionEffectivenessRecord.objects.all()
    mem_qs = OrganizationalMemory.objects.all()
    if board_id:
        eff_qs = eff_qs.filter(board_id=board_id)
        mem_qs = mem_qs.filter(board_id=board_id)

    total_actions = eff_qs.count()

    # Effectiveness component
    if total_actions > 0:
        avg_eff = eff_qs.aggregate(v=Avg("effectiveness_score"))["v"] or 0
        success_rate = eff_qs.filter(outcome_label=OUTCOME_SUCCESS).count() / total_actions
        effectiveness_component = min(100, avg_eff * 0.6 + success_rate * 100 * 0.4)
    else:
        effectiveness_component = 0.0

    # SLA component (from measured sla improvements)
    if total_actions > 0:
        avg_sla_before = eff_qs.aggregate(v=Avg("sla_before"))["v"] or 0
        avg_sla_after = eff_qs.aggregate(v=Avg("sla_after"))["v"] or 0
        sla_improvement = max(0, avg_sla_before - avg_sla_after)
        sla_component = min(100, 50 + sla_improvement * 0.5)
    else:
        sla_component = 50.0

    # Risk component (lower residual risk = higher maturity)
    if total_actions > 0:
        avg_risk_after = eff_qs.aggregate(v=Avg("risk_after"))["v"] or 50
        risk_component = max(0, 100 - avg_risk_after)
    else:
        risk_component = 50.0

    # Productivity (execution time — faster resolution = higher)
    if total_actions > 0:
        avg_time = eff_qs.aggregate(v=Avg("execution_time"))["v"] or 0
        if avg_time < 3600:
            productivity_component = 90
        elif avg_time < 86400:
            productivity_component = 70
        else:
            productivity_component = 50
    else:
        productivity_component = 50.0

    # Learning component (memories + playbooks accumulated)
    memory_count = mem_qs.count()
    lesson_count = mem_qs.filter(memory_type="lesson_learned").count()
    playbook_count = mem_qs.filter(memory_type="playbook_candidate").count()
    learning_component = min(100, lesson_count * 5 + playbook_count * 10 + memory_count * 2)

    weights = {"sla": 0.2, "effectiveness": 0.3, "risk": 0.2, "productivity": 0.15, "learning": 0.15}
    index = (
        sla_component * weights["sla"]
        + effectiveness_component * weights["effectiveness"]
        + risk_component * weights["risk"]
        + productivity_component * weights["productivity"]
        + learning_component * weights["learning"]
    )

    return {
        "eor_maturity_index": round(index, 1),
        "components": {
            "sla": round(sla_component, 1),
            "effectiveness": round(effectiveness_component, 1),
            "risk": round(risk_component, 1),
            "productivity": round(productivity_component, 1),
            "learning": round(learning_component, 1),
        },
        "evidence": {
            "total_action_records": total_actions,
            "organizational_memories": memory_count,
            "lessons_learned": lesson_count,
            "playbook_candidates": playbook_count,
        },
        "board_id": board_id or "all",
    }
