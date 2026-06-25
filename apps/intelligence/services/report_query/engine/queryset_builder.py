from __future__ import annotations

from django.db.models import Q, QuerySet

from apps.intelligence.services.report_query.domain.filters import (
    LabelOperator,
    MemberRole,
    ReportQueryPayload,
    StatusOperator,
)
from apps.intelligence.services.report_query.domain.periods import resolve_period
from apps.intelligence.services.report_query.domain.title_parser import compile_title_filter, title_matches
from apps.intelligence.services.report_query.domain.status_aliases import resolve_status_filter
from apps.intelligence.services.report_query.engine.card_metrics import (
    card_matches_checklist,
    card_matches_priority,
    card_matches_risk,
    card_matches_score,
    card_matches_status,
    card_member_matches,
    get_card_label_names,
)
from integrations.trello.models import Action, Card


def build_filtered_cards(payload: ReportQueryPayload) -> tuple[list[Card], dict]:
    """
    Apply all filters and return matching cards plus filter metadata.
    """
    if not payload.board_id:
        return [], {"error": "board_id required"}

    qs = (
        Card.objects.filter(board__trello_id=payload.board_id, is_removed=False)
        .select_related("board", "board_list")
        .prefetch_related("assignees")
    )

    date_range = resolve_period(
        preset=payload.period,
        date_from=payload.date_from,
        date_to=payload.date_to,
    )
    if date_range:
        qs = _filter_by_period(qs, payload.board_id, date_range.start, date_range.end)

    if payload.lists:
        qs = qs.filter(status__in=payload.lists)

    if payload.members and payload.member_role == MemberRole.ASSIGNEE:
        member_q = Q()
        for name in payload.members:
            member_q |= (
                Q(assignees__trello_id__iexact=name)
                | Q(assignees__full_name__icontains=name)
                | Q(assignees__username__icontains=name)
            )
        qs = qs.filter(member_q).distinct()

    cards = list(qs)
    meta = {
        "board_id": payload.board_id,
        "date_range": {
            "from": date_range.start.isoformat() if date_range else None,
            "to": date_range.end.isoformat() if date_range else None,
        },
        "initial_count": len(cards),
    }

    title_filter = compile_title_filter(
        payload.title_contains,
        payload.title_prefix,
        payload.title_filter,
    )

    filtered: list[Card] = []
    for card in cards:
        if not title_matches(title_filter, card.title):
            continue
        if payload.labels and not _labels_match(card, payload.labels, payload.label_operator):
            continue
        if payload.members and payload.member_role != MemberRole.ASSIGNEE:
            if not card_member_matches(card, payload.members, payload.member_role):
                continue
        if payload.status:
            resolved = [resolve_status_filter(s) for s in payload.status]
            resolved = [r for r in resolved if r]
            if resolved:
                matches = [card_matches_status(card, r) for r in resolved]
                if payload.status_operator == StatusOperator.AND:
                    if not all(matches):
                        continue
                elif not any(matches):
                    continue
        if payload.priority and not any(
            card_matches_priority(card, p) for p in payload.priority
        ):
            continue
        if payload.checklist and not card_matches_checklist(card, payload.checklist):
            continue
        if payload.risk_levels and not any(
            card_matches_risk(card, r) for r in payload.risk_levels
        ):
            continue
        if payload.score_range and not card_matches_score(card, payload.score_range):
            continue
        filtered.append(card)

    meta["matched_count"] = len(filtered)
    meta["filters_applied"] = payload.to_cache_key_dict()
    return filtered, meta


def _filter_by_period(qs: QuerySet, board_id: str, start, end) -> QuerySet:
    action_card_ids = Action.objects.filter(
        board__trello_id=board_id,
        occurred_at__gte=start,
        occurred_at__lte=end,
    ).values_list("raw_json__data__card__id", flat=True)

    return qs.filter(
        Q(created_at__gte=start, created_at__lte=end)
        | Q(completed_at__gte=start, completed_at__lte=end)
        | Q(last_activity_at__gte=start, last_activity_at__lte=end)
        | Q(trello_id__in=[cid for cid in action_card_ids if cid])
    ).distinct()


def _labels_match(card: Card, labels: list[str], operator: LabelOperator) -> bool:
    card_labels = {name.lower() for name in get_card_label_names(card)}
    wanted = {label.lower() for label in labels}
    if not wanted:
        return True
    if operator == LabelOperator.AND:
        return wanted.issubset(card_labels)
    return bool(wanted & card_labels)
