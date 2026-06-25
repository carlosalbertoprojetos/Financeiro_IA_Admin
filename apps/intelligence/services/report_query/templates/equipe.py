from __future__ import annotations

from typing import Any

from apps.intelligence.services.report_query.templates import membro as membro_template


def generate(
    *,
    cards: list,
    card_records: list,
    actions: list,
    board_id: str,
    filters_meta: dict[str, Any],
) -> dict[str, Any]:
    result = membro_template.generate(
        cards=cards,
        card_records=card_records,
        actions=actions,
        board_id=board_id,
        filters_meta=filters_meta,
    )
    result["report_type"] = "EQUIPE"
    result["team_size"] = len(result.get("members", []))
    return result
