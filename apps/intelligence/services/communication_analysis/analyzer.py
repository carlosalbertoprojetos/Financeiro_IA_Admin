"""Communication analyzer — extracts decisions, risks, and pending items from comments."""

from __future__ import annotations

import re

from apps.intelligence.domain.entities import CommunicationAnalysis
from integrations.trello.models import Action, Card

DECISION_PATTERNS = [
    re.compile(r"\b(decidimos|decidido|aprovado|approved|decision|fechado que)\b", re.I),
    re.compile(r"\b(vamos seguir|ok para|confirmado)\b", re.I),
]
PENDING_PATTERNS = [
    re.compile(r"\b(pendente|pending|aguardando|falta|precisamos)\b", re.I),
    re.compile(r"\b(todo|to-do|a fazer)\b", re.I),
]
RISK_PATTERNS = [
    re.compile(r"\b(risco|risk|atraso|delay|problema|issue)\b", re.I),
    re.compile(r"\b(preocupa|concern|impedimento)\b", re.I),
]
REQUEST_PATTERNS = [
    re.compile(r"\?"),
    re.compile(r"\b(pode|could you|preciso que|please|por favor)\b", re.I),
]
ESCALATION_PATTERNS = [
    re.compile(r"\b(escala|escalat|urgente|crítico|critico|diretoria|ceo)\b", re.I),
]
DEPENDENCY_PATTERNS = [
    re.compile(r"\b(depende|dependency|aguardando|waiting on|bloqueado por)\b", re.I),
    re.compile(r"\b(externo|third.?party|fornecedor|vendor)\b", re.I),
]
BLOCKER_PATTERNS = [
    re.compile(r"\b(bloqueio|blocker|blocked|impedimento)\b", re.I),
]


def analyze_communication(card: Card) -> CommunicationAnalysis:
    """Analyze card comments for executive communication insights."""
    comments = _load_comment_texts(card)
    if not comments:
        return CommunicationAnalysis(
            card_id=card.trello_id,
            executive_summary="Sem comunicação registrada nos comentários.",
            comment_count=0,
        )

    decisions: list[str] = []
    pending: list[str] = []
    risks: list[str] = []
    unanswered: list[str] = []
    dependencies: list[str] = []
    escalations: list[str] = []

    for idx, text in enumerate(comments):
        snippet = _snippet(text)
        if _matches_any(text, DECISION_PATTERNS):
            decisions.append(snippet)
        if _matches_any(text, PENDING_PATTERNS):
            pending.append(snippet)
        if _matches_any(text, RISK_PATTERNS) or _matches_any(text, BLOCKER_PATTERNS):
            risks.append(snippet)
        if _matches_any(text, REQUEST_PATTERNS) and not _has_later_response(comments, idx):
            unanswered.append(snippet)
        if _matches_any(text, DEPENDENCY_PATTERNS):
            dependencies.append(snippet)
        if _matches_any(text, ESCALATION_PATTERNS):
            escalations.append(snippet)

    summary_parts = [f"{len(comments)} comentário(s) analisado(s)."]
    if decisions:
        summary_parts.append(f"{len(decisions)} decisão(ões) identificada(s).")
    if risks:
        summary_parts.append(f"{len(risks)} risco(s) ou bloqueio(s) mencionado(s).")
    if unanswered:
        summary_parts.append(f"{len(unanswered)} solicitação(ões) sem resposta aparente.")

    return CommunicationAnalysis(
        card_id=card.trello_id,
        executive_summary=" ".join(summary_parts),
        decisions=tuple(decisions[:10]),
        pending_items=tuple(pending[:10]),
        risks=tuple(risks[:10]),
        unanswered_requests=tuple(unanswered[:10]),
        external_dependencies=tuple(dependencies[:10]),
        escalations_needed=tuple(escalations[:10]),
        comment_count=len(comments),
    )


def analyze_board_communication(board_trello_id: str) -> list[CommunicationAnalysis]:
    cards = Card.objects.filter(board__trello_id=board_trello_id, is_removed=False)
    return [analyze_communication(card) for card in cards]


def _load_comment_texts(card: Card) -> list[str]:
    actions = Action.objects.filter(
        board_id=card.board_id,
        action_type="commentCard",
    ).order_by("occurred_at")
    texts: list[str] = []
    for action in actions:
        data = (action.raw_json or {}).get("data") or {}
        card_data = data.get("card") or {}
        if card_data.get("id") != card.trello_id:
            continue
        text = (data.get("text") or "").strip()
        if text:
            texts.append(text)
    return texts


def _matches_any(text: str, patterns: list[re.Pattern[str]]) -> bool:
    return any(p.search(text) for p in patterns)


def _snippet(text: str, max_len: int = 120) -> str:
    cleaned = " ".join(text.split())
    return cleaned[:max_len] + ("..." if len(cleaned) > max_len else "")


def _has_later_response(comments: list[str], question_idx: int) -> bool:
    if question_idx >= len(comments) - 1:
        return False
    return len(comments) > question_idx + 1
