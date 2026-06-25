"""Data enrichment engine — transforms raw card data into executive context."""

from __future__ import annotations

import re
from typing import Any

from apps.intelligence.domain.entities import CardContext
from apps.intelligence.models import CardEnrichment
from integrations.trello.models import Action, Card

HIGH_KEYWORDS = frozenset(
    {
        "urgente",
        "urgent",
        "crítico",
        "critico",
        "critical",
        "blocker",
        "bloqueio",
        "prioridade alta",
        "p0",
        "p1",
        "asap",
        "imediato",
        "produção",
        "producao",
        "incidente",
        "outage",
    }
)
LOW_KEYWORDS = frozenset(
    {
        "baixa",
        "low",
        "nice to have",
        "backlog",
        "futuro",
        "melhoria",
        "opcional",
        "p4",
        "p5",
    }
)
AREA_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("TI", re.compile(r"\b(ti|tech|dev|engenharia|infra|backend|frontend)\b", re.I)),
    ("Financeiro", re.compile(r"\b(financeiro|financ|contabil|fiscal|pagamento)\b", re.I)),
    ("Comercial", re.compile(r"\b(comercial|vendas|sales|cliente|crm)\b", re.I)),
    ("Operações", re.compile(r"\b(operaç|operac|logística|logistica|supply)\b", re.I)),
    ("RH", re.compile(r"\b(rh|people|recursos humanos|contratação)\b", re.I)),
    ("Jurídico", re.compile(r"\b(jurídico|juridico|legal|compliance)\b", re.I)),
]
CLIENT_PATTERN = re.compile(r"\b(cliente|client|account)[:\s]+([^\n,;]+)", re.I)
PROJECT_PATTERN = re.compile(r"\b(projeto|project|epic)[:\s]+([^\n,;]+)", re.I)
BLOCKER_PATTERN = re.compile(r"\b(bloqueio|blocker|impedimento|blocked)\b", re.I)


def enrich_card(card: Card, *, persist: bool = True) -> CardContext:
    """Extract executive context from card title, description, labels, and comments."""
    comments = _load_comments(card)
    text_blob = _build_text_blob(card, comments)
    labels_text = " ".join(str(label.get("name", "")) for label in (card.labels or []))

    priority = _detect_level(text_blob + " " + labels_text, HIGH_KEYWORDS, LOW_KEYWORDS)
    urgency = _detect_urgency(text_blob, card)
    complexity = _detect_complexity(text_blob, comments)
    impact = _detect_impact(text_blob, labels_text)
    area = _detect_area(text_blob + " " + labels_text)
    client = _extract_match(CLIENT_PATTERN, text_blob)
    project = _extract_match(PROJECT_PATTERN, text_blob)
    objective = _extract_objective(card)
    signals = _collect_signals(text_blob, labels_text, card)

    confidence = min(1.0, 0.3 + len(signals) * 0.1 + (0.2 if labels_text.strip() else 0))

    context = CardContext(
        card_id=card.trello_id,
        title=card.title,
        objective=objective,
        area=area,
        department=area,
        project=project,
        client=client,
        priority=priority,
        urgency=urgency,
        complexity=complexity,
        impact=impact,
        criticality=_merge_levels(priority, urgency),
        business_value=impact,
        confidence=round(confidence, 2),
        signals=tuple(signals),
    )

    if persist:
        _persist_enrichment(card, context)

    return context


def enrich_board(board_trello_id: str) -> list[CardContext]:
    """Enrich all active cards on a board."""
    cards = Card.objects.filter(board__trello_id=board_trello_id, is_removed=False)
    return [enrich_card(card) for card in cards]


def _persist_enrichment(card: Card, context: CardContext) -> None:
    CardEnrichment.objects.update_or_create(
        card=card,
        defaults={
            "objective": context.objective,
            "area": context.area,
            "department": context.department,
            "project": context.project,
            "client": context.client,
            "priority": context.priority,
            "urgency": context.urgency,
            "complexity": context.complexity,
            "impact": context.impact,
            "criticality": context.criticality,
            "business_value": context.business_value,
            "confidence": context.confidence,
            "signals_json": list(context.signals),
            "context_json": {
                "title": context.title,
                "detected_at": card.updated_at.isoformat() if card.updated_at else None,
            },
        },
    )


def _load_comments(card: Card) -> list[str]:
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
        text = data.get("text") or ""
        if text:
            texts.append(text)
    return texts


def _build_text_blob(card: Card, comments: list[str]) -> str:
    parts = [card.title or "", card.description or "", *comments]
    return "\n".join(parts).lower()


def _detect_level(text: str, high: frozenset[str], low: frozenset[str]) -> str:
    for keyword in high:
        if keyword in text:
            return "ALTA"
    for keyword in low:
        if keyword in text:
            return "BAIXA"
    return "MÉDIA"


def _detect_urgency(text: str, card: Card) -> str:
    if BLOCKER_PATTERN.search(text):
        return "ALTA"
    if card.due_at:
        from django.utils import timezone

        if card.due_at < timezone.now() and not card.completed_at:
            return "ALTA"
    return _detect_level(text, HIGH_KEYWORDS, LOW_KEYWORDS)


def _detect_complexity(text: str, comments: list[str]) -> str:
    score = 0
    if len(text) > 500:
        score += 1
    if len(comments) > 5:
        score += 1
    if any(kw in text for kw in ("integração", "integracao", "migração", "migracao", "refactor")):
        score += 1
    if score >= 2:
        return "ALTA"
    if score == 1:
        return "MÉDIA"
    return "BAIXA"


def _detect_impact(text: str, labels: str) -> str:
    combined = f"{text} {labels}".lower()
    if any(kw in combined for kw in ("revenue", "receita", "cliente", "sla", "produção", "producao")):
        return "ALTA"
    if any(kw in combined for kw in ("interno", "documentação", "documentacao")):
        return "BAIXA"
    return "MÉDIA"


def _detect_area(text: str) -> str:
    for name, pattern in AREA_PATTERNS:
        if pattern.search(text):
            return name
    return ""


def _extract_match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return match.group(2).strip() if match else ""


def _extract_objective(card: Card) -> str:
    if card.description:
        first_line = card.description.strip().split("\n")[0]
        if len(first_line) > 10:
            return first_line[:500]
    return card.title or ""


def _collect_signals(text: str, labels: str, card: Card) -> list[str]:
    signals: list[str] = []
    if BLOCKER_PATTERN.search(text):
        signals.append("blocker_mentioned")
    if card.due_at and not card.completed_at:
        signals.append("has_due_date")
    if card.labels:
        signals.append("has_labels")
    for keyword in HIGH_KEYWORDS:
        if keyword in text:
            signals.append(f"keyword:{keyword}")
            break
    return signals


def _merge_levels(a: str, b: str) -> str:
    levels = {"BAIXA": 0, "MÉDIA": 1, "ALTA": 2}
    max_level = max(levels.get(a, 1), levels.get(b, 1))
    return {0: "BAIXA", 1: "MÉDIA", 2: "ALTA"}[max_level]
