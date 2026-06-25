from __future__ import annotations

from typing import Any

from apps.intelligence.services.report_query.templates import (
    etiqueta,
    executivo,
    membro,
    prefixo,
)


def generate(
    *,
    cards: list,
    card_records: list,
    actions: list,
    board_id: str,
    filters_meta: dict[str, Any],
) -> dict[str, Any]:
    """Cross-dimensional analysis combining prefix, label, member and period filters."""
    return {
        "report_type": "MULTIDIMENSIONAL",
        "dimensions": {
            "executive": executivo.generate(
                cards=cards,
                card_records=card_records,
                actions=actions,
                board_id=board_id,
                filters_meta=filters_meta,
            ),
            "by_member": membro.generate(
                cards=cards,
                card_records=card_records,
                actions=actions,
                board_id=board_id,
                filters_meta=filters_meta,
            ),
            "by_label": etiqueta.generate(
                cards=cards,
                card_records=card_records,
                actions=actions,
                board_id=board_id,
                filters_meta=filters_meta,
            ),
            "by_prefix": prefixo.generate(
                cards=cards,
                card_records=card_records,
                actions=actions,
                board_id=board_id,
                filters_meta=filters_meta,
            ),
        },
        "card_count": len(cards),
        "filters": filters_meta,
    }
