from __future__ import annotations

from typing import Any

from apps.intelligence.models import DecisionEffectivenessRecord, OrganizationalMemory


def build_knowledge_graph(*, board_id: str = "", limit: int = 100) -> dict[str, Any]:
    """
    Build problem → action → result → effectiveness graph from real records.
    """
    qs = DecisionEffectivenessRecord.objects.all().order_by("-created_at")
    if board_id:
        qs = qs.filter(board_id=board_id)
    records = list(qs[:limit])

    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    for rec in records:
        problem_id = f"problem:{rec.category or 'GENERAL'}:{rec.decision_id[:8]}"
        action_id = f"action:{rec.action_type}"
        result_id = f"result:{rec.outcome_label}:{rec.id}"
        eff_id = f"effectiveness:{rec.id}"

        nodes[problem_id] = {
            "id": problem_id,
            "type": "problem",
            "label": rec.context_json.get("insight", rec.category or "Operational issue")[:120],
            "category": rec.category,
            "risk_before": rec.risk_before,
        }
        nodes[action_id] = {"id": action_id, "type": "action", "label": rec.action_type}
        nodes[result_id] = {
            "id": result_id,
            "type": "result",
            "label": rec.outcome_label,
            "risk_after": rec.risk_after,
        }
        nodes[eff_id] = {
            "id": eff_id,
            "type": "effectiveness",
            "label": f"score={rec.effectiveness_score}",
            "score": rec.effectiveness_score,
        }

        edges.extend([
            {"from": problem_id, "to": action_id, "relation": "triggered"},
            {"from": action_id, "to": result_id, "relation": "produced"},
            {"from": result_id, "to": eff_id, "relation": "measured_as"},
        ])

    memories = OrganizationalMemory.objects.all()
    if board_id:
        memories = memories.filter(board_id=board_id)
    for mem in memories[:20]:
        mem_id = f"memory:{mem.memory_key}"
        nodes[mem_id] = {
            "id": mem_id,
            "type": "lesson",
            "label": mem.title[:120],
            "memory_type": mem.memory_type,
        }
        if mem.related_action_type:
            action_id = f"action:{mem.related_action_type}"
            edges.append({"from": mem_id, "to": action_id, "relation": "recommends"})

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "stats": {
            "problems": sum(1 for n in nodes.values() if n["type"] == "problem"),
            "actions": sum(1 for n in nodes.values() if n["type"] == "action"),
            "results": sum(1 for n in nodes.values() if n["type"] == "result"),
        },
    }
