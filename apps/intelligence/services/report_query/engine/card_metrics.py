from __future__ import annotations

from django.utils import timezone

from apps.intelligence.models import CardEnrichment
from apps.intelligence.services.checklist.intelligence import analyze_checklists
from apps.intelligence.services.report_query.domain.filters import (
    CardStatusFilter,
    ChecklistFilter,
    ScoreRange,
)
from apps.intelligence.services.risk_engine.scorer import assess_card_risk
from integrations.trello.models import Action, Card

DONE_STATUSES = frozenset({"done", "concluído", "concluido", "completed", "finalizado", "concluido"})
BLOCKED_KEYWORDS = frozenset({"blocked", "bloqueado", "bloqueio", "impedimento"})


def get_card_label_names(card: Card) -> list[str]:
    return [str(label.get("name", "")) for label in (card.labels or []) if label.get("name")]


def card_matches_status(card: Card, status: CardStatusFilter) -> bool:
    now = timezone.now()
    status_lower = (card.status or "").lower()
    is_done = card.is_closed or status_lower in DONE_STATUSES

    if status == CardStatusFilter.OPEN:
        return not is_done and not card.is_removed
    if status == CardStatusFilter.IN_PROGRESS:
        return not is_done and any(
            kw in status_lower for kw in ("progress", "andamento", "doing", "dev")
        )
    if status == CardStatusFilter.BLOCKED:
        return any(kw in status_lower for kw in BLOCKED_KEYWORDS)
    if status == CardStatusFilter.COMPLETED:
        return is_done
    if status == CardStatusFilter.OVERDUE:
        return bool(card.due_at and card.due_at < now and not is_done)
    if status == CardStatusFilter.CANCELLED:
        return card.is_removed or "cancel" in status_lower
    if status == CardStatusFilter.REOPENED:
        return card.timeline_events.filter(event_type="CARD_REOPENED").exists()
    return False


def card_matches_priority(card: Card, priority: str) -> bool:
    enrichment = CardEnrichment.objects.filter(card=card).first()
    if enrichment:
        card_priority = enrichment.priority.lower().replace("é", "e")
    else:
        from apps.intelligence.services.enrichment.engine import enrich_card

        ctx = enrich_card(card, persist=False)
        card_priority = ctx.priority.lower().replace("é", "e")

    mapping = {
        "baixa": "baixa",
        "media": "media",
        "média": "media",
        "alta": "alta",
        "critica": "alta",
        "crítica": "alta",
    }
    normalized = mapping.get(priority.lower(), priority.lower())
    normalized_card = mapping.get(card_priority, card_priority)
    if normalized == "critica":
        return normalized_card == "alta"
    return normalized_card == normalized


def card_matches_checklist(card: Card, checklist_filter: ChecklistFilter) -> bool:
    metrics = analyze_checklists(card)
    has_checklist = metrics.total_items > 0

    if checklist_filter == ChecklistFilter.WITH_CHECKLIST:
        return has_checklist
    if checklist_filter == ChecklistFilter.WITHOUT_CHECKLIST:
        return not has_checklist
    if checklist_filter == ChecklistFilter.COMPLETED:
        return has_checklist and metrics.completion_pct >= 100
    if checklist_filter == ChecklistFilter.PENDING:
        return has_checklist and metrics.pending_items > 0
    if checklist_filter == ChecklistFilter.BLOCKED:
        return bool(metrics.blocked_items)
    return True


def card_matches_risk(card: Card, risk_level: str) -> bool:
    assessment = assess_card_risk(card)
    level_map = {
        "baixo": "Baixo",
        "moderado": "Moderado",
        "alto": "Alto",
        "critico": "Crítico",
        "crítico": "Crítico",
    }
    return assessment.level == level_map.get(risk_level.lower(), risk_level)


def card_matches_score(card: Card, score_range: ScoreRange) -> bool:
    """Map risk score (0-100 high=bad) to EOR-like score (100 - risk)."""
    assessment = assess_card_risk(card)
    eor_score = max(0, 100 - assessment.score)
    return score_range.min_score <= eor_score <= score_range.max_score


def card_member_matches(card: Card, members: list[str], role: str) -> bool:
    from apps.intelligence.services.report_query.domain.filters import MemberRole

    member_set = {m.lower() for m in members}

    if role == MemberRole.ASSIGNEE:
        for assignee in card.assignees.all():
            if _member_in_set(assignee, member_set):
                return True
        return False

    actions = Action.objects.filter(board_id=card.board_id).order_by("occurred_at")
    card_actions = [
        a
        for a in actions
        if (a.raw_json.get("data") or {}).get("card", {}).get("id") == card.trello_id
    ]

    if role == MemberRole.CREATOR:
        for action in card_actions:
            if action.action_type == "createCard" and action.member and _member_in_set(action.member, member_set):
                return True
        return False

    if role == MemberRole.COMMENTER:
        for action in card_actions:
            if action.action_type == "commentCard" and action.member and _member_in_set(action.member, member_set):
                return True
        return False

    if role == MemberRole.LAST_EDITOR:
        editors = [a for a in card_actions if a.action_type == "updateCard" and a.member]
        if editors and _member_in_set(editors[-1].member, member_set):
            return True
        return False

    if role == MemberRole.PARTICIPANT:
        for action in card_actions:
            if action.member and _member_in_set(action.member, member_set):
                return True
        return False

    if role == MemberRole.EXECUTOR:
        for action in card_actions:
            if action.action_type in ("updateCheckItemStateOnCard", "updateCard") and action.member:
                if _member_in_set(action.member, member_set):
                    return True
        return False

    return False


def _member_in_set(member, member_set: set[str]) -> bool:
    candidates = {
        member.trello_id.lower(),
        (member.full_name or "").lower(),
        (member.username or "").lower(),
    }
    return bool(candidates & member_set)
