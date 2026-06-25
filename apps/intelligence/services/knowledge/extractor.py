"""Knowledge extraction engine — builds operational knowledge base."""

from __future__ import annotations

from typing import Any

from apps.intelligence.models import KnowledgeBaseEntry
from apps.intelligence.services.bottleneck_detector.detector import detect_bottlenecks
from apps.intelligence.services.communication_analysis.analyzer import analyze_communication
from apps.intelligence.services.risk_engine.scorer import assess_board_risk
from integrations.trello.models import Board, Card


def extract_board_knowledge(board: Board | str) -> list[KnowledgeBaseEntry]:
    """Extract and persist knowledge entries for a board."""
    if isinstance(board, str):
        board = Board.objects.get(trello_id=board)

    entries: list[KnowledgeBaseEntry] = []
    entries.extend(_extract_from_bottlenecks(board))
    entries.extend(_extract_from_risks(board))
    entries.extend(_extract_from_cards(board))
    return entries


def _extract_from_bottlenecks(board: Board) -> list[KnowledgeBaseEntry]:
    bottlenecks = detect_bottlenecks(board_trello_id=board.trello_id)
    entries: list[KnowledgeBaseEntry] = []

    for item in bottlenecks.get("congested_lists", []):
        entry, _ = KnowledgeBaseEntry.objects.update_or_create(
            board=board,
            entry_type=KnowledgeBaseEntry.EntryType.OPERATIONAL_PATTERN,
            title=f"Congestionamento em {item['list']}",
            defaults={
                "content": f"Lista '{item['list']}' com WIP={item['wip']}. Severidade: {item['severity']}.",
                "confidence": 0.8,
                "metadata_json": item,
            },
        )
        entries.append(entry)

    for item in bottlenecks.get("recurring_rework", []):
        entry, _ = KnowledgeBaseEntry.objects.update_or_create(
            board=board,
            entry_type=KnowledgeBaseEntry.EntryType.RECURRING_PROBLEM,
            title=f"Retrabalho recorrente — card {item['card_id']}",
            defaults={
                "content": f"Card movido {item['move_count']} vezes, indicando possível retrabalho.",
                "confidence": 0.7,
                "metadata_json": item,
            },
        )
        entries.append(entry)

    return entries


def _extract_from_risks(board: Board) -> list[KnowledgeBaseEntry]:
    risk_data = assess_board_risk(board_trello_id=board.trello_id)
    entries: list[KnowledgeBaseEntry] = []

    for assessment in risk_data.get("assessments", []):
        if assessment["score"] < 50:
            continue
        factors = ", ".join(f["factor"] for f in assessment.get("factors", []))
        entry, _ = KnowledgeBaseEntry.objects.update_or_create(
            board=board,
            entry_type=KnowledgeBaseEntry.EntryType.ROOT_CAUSE,
            title=f"Risco {assessment['level']} — {assessment['card_id']}",
            defaults={
                "content": f"Score {assessment['score']}. Fatores: {factors}.",
                "confidence": assessment["score"] / 100,
                "metadata_json": assessment,
            },
        )
        entries.append(entry)

    return entries


def _extract_from_cards(board: Board) -> list[KnowledgeBaseEntry]:
    entries: list[KnowledgeBaseEntry] = []
    completed = Card.objects.filter(board=board, is_closed=True, is_removed=False)[:20]

    for card in completed:
        comm = analyze_communication(card)
        if comm.decisions:
            entry, _ = KnowledgeBaseEntry.objects.update_or_create(
                board=board,
                card=card,
                entry_type=KnowledgeBaseEntry.EntryType.LESSON_LEARNED,
                title=f"Decisões em: {card.title[:80]}",
                defaults={
                    "content": "; ".join(comm.decisions[:3]),
                    "confidence": 0.6,
                    "metadata_json": {"decisions": list(comm.decisions)},
                },
            )
            entries.append(entry)

        if comm.risks and card.completed_at:
            entry, _ = KnowledgeBaseEntry.objects.update_or_create(
                board=board,
                card=card,
                entry_type=KnowledgeBaseEntry.EntryType.BEST_PRACTICE,
                title=f"Riscos mitigados: {card.title[:80]}",
                defaults={
                    "content": f"Card concluído apesar de riscos: {'; '.join(comm.risks[:2])}",
                    "confidence": 0.5,
                    "metadata_json": {"risks": list(comm.risks)},
                },
            )
            entries.append(entry)

    return entries


def get_knowledge_base(board_trello_id: str) -> list[dict[str, Any]]:
    """Return knowledge base entries as dicts."""
    entries = KnowledgeBaseEntry.objects.filter(board__trello_id=board_trello_id).order_by("-created_at")
    return [
        {
            "id": entry.pk,
            "type": entry.entry_type,
            "title": entry.title,
            "content": entry.content,
            "confidence": entry.confidence,
            "card_id": entry.card.trello_id if entry.card else None,
            "created_at": entry.created_at.isoformat(),
        }
        for entry in entries[:100]
    ]
