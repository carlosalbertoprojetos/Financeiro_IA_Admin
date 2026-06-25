from __future__ import annotations

from typing import Any

from apps.intelligence.services.enrichment.engine import enrich_card
from apps.intelligence.services.report_query.templates import executivo


def generate(
    *,
    cards: list,
    card_records: list,
    actions: list,
    board_id: str,
    filters_meta: dict[str, Any],
) -> dict[str, Any]:
    by_client: dict[str, list] = {}
    for card in cards:
        ctx = enrich_card(card, persist=False)
        client = ctx.client or "Não identificado"
        by_client.setdefault(client, []).append(card)

    clients = [
        {"client": name, "card_count": len(client_cards)}
        for name, client_cards in sorted(by_client.items(), key=lambda x: len(x[1]), reverse=True)
    ]

    base = executivo.generate(
        cards=cards,
        card_records=card_records,
        actions=actions,
        board_id=board_id,
        filters_meta=filters_meta,
    )
    base["report_type"] = "CLIENTE"
    base["clients"] = clients
    return base
