from __future__ import annotations

from typing import Any, Callable

from analytics.adapters import cards_to_records, actions_to_records
from apps.intelligence.services.report_query.domain.filters import ReportTemplate
from apps.intelligence.services.report_query.templates import (
    cliente,
    equipe,
    etiqueta,
    executivo,
    membro,
    multidimensional,
    operacional,
    prefixo,
    produtividade,
    riscos,
    sla,
)
from integrations.trello.models import Action, Card

GENERATORS: dict[ReportTemplate, Callable[..., dict[str, Any]]] = {
    ReportTemplate.EXECUTIVO: executivo.generate,
    ReportTemplate.OPERACIONAL: operacional.generate,
    ReportTemplate.MEMBRO: membro.generate,
    ReportTemplate.EQUIPE: equipe.generate,
    ReportTemplate.ETIQUETA: etiqueta.generate,
    ReportTemplate.PROJETO: prefixo.generate,
    ReportTemplate.CLIENTE: cliente.generate,
    ReportTemplate.RISCOS: riscos.generate,
    ReportTemplate.SLA: sla.generate,
    ReportTemplate.PRODUTIVIDADE: produtividade.generate,
    ReportTemplate.PREFIXO: prefixo.generate,
    ReportTemplate.MULTIDIMENSIONAL: multidimensional.generate,
}


def generate_report(
    template: ReportTemplate,
    cards: list[Card],
    *,
    board_id: str,
    filters_meta: dict[str, Any],
) -> dict[str, Any]:
    generator = GENERATORS.get(template, executivo.generate)
    board_actions = list(
        Action.objects.filter(board__trello_id=board_id).order_by("occurred_at")
    )
    card_records = cards_to_records(cards)
    action_records = actions_to_records(board_actions)
    card_ids = {c.trello_id for c in cards}
    scoped_actions = [a for a in action_records if a.card_id in card_ids]

    return generator(
        cards=cards,
        card_records=card_records,
        actions=scoped_actions,
        board_id=board_id,
        filters_meta=filters_meta,
    )
